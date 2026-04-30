"""Audit logging service."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import AuditRequest, AuditViolation
from ..models import QueryRequest, QueryResponse, AuditRecord, SummaryStats
from .audit_encryption import encrypt_field, decrypt_field


class AuditLogger:
    """Log all requests and decisions to audit database."""

    def __init__(self, db: Session):
        self.db = db

    def log_request(
        self,
        request: QueryRequest,
        response: QueryResponse,
        policy_decision: str,
        duration_ms: int,
        error_message: str = None,
    ):
        """Log a completed request to audit database."""
        audit_record = AuditRequest(
            timestamp=datetime.utcnow(),
            user_id=request.user_id,
            prompt=encrypt_field(request.prompt),
            response=encrypt_field(response.response if response else ""),
            model_used=response.model_used if response else "",
            tokens_in=response.tokens_in if response else 0,
            tokens_out=response.tokens_out if response else 0,
            cost_usd=response.cost_usd if response else 0.0,
            policy_decision=policy_decision,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self.db.add(audit_record)
        self.db.commit()

    def log_policy_rejection(
        self,
        user_id: str,
        reason: str,
        prompt_summary: str = None,
    ):
        """Log a policy rejection."""
        violation = AuditViolation(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            violation_reason=reason,
            details=prompt_summary or "",
        )
        self.db.add(violation)
        self.db.commit()

    def get_user_requests(self, user_id: str, hours: int = 1) -> list[AuditRecord]:
        """Get recent requests for a user."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        records = self.db.query(AuditRequest).filter(
            AuditRequest.user_id == user_id,
            AuditRequest.timestamp >= cutoff,
        ).order_by(AuditRequest.timestamp.desc()).all()

        return [
            AuditRecord(
                id=r.id,
                timestamp=r.timestamp,
                user_id=r.user_id,
                prompt_summary=r.prompt[:100] if r.prompt else "",
                model_used=r.model_used,
                tokens_in=r.tokens_in,
                tokens_out=r.tokens_out,
                cost_usd=r.cost_usd,
                policy_decision=r.policy_decision,
                duration_ms=r.duration_ms,
                error_message=r.error_message,
            )
            for r in records
        ]

    def get_daily_summary(self, days: int = 1) -> SummaryStats:
        """Get cost and usage summary."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Total requests
        total_requests = self.db.query(func.count(AuditRequest.id)).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision == "approved",
        ).scalar() or 0

        # Total cost
        total_cost = self.db.query(func.sum(AuditRequest.cost_usd)).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision == "approved",
        ).scalar() or 0

        # Total tokens
        total_tokens = self.db.query(
            func.sum(AuditRequest.tokens_in + AuditRequest.tokens_out)
        ).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision == "approved",
        ).scalar() or 0

        # By model
        model_stats = self.db.query(
            AuditRequest.model_used,
            func.count(AuditRequest.id).label("count"),
            func.sum(AuditRequest.cost_usd).label("cost"),
        ).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision == "approved",
        ).group_by(AuditRequest.model_used).all()

        requests_by_model = {m[0]: m[1] for m in model_stats}
        cost_by_model = {m[0]: m[2] for m in model_stats}

        # Top users
        user_stats = self.db.query(
            AuditRequest.user_id,
            func.count(AuditRequest.id).label("count"),
            func.sum(AuditRequest.cost_usd).label("cost"),
        ).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision == "approved",
        ).group_by(AuditRequest.user_id).order_by(
            func.sum(AuditRequest.cost_usd).desc()
        ).limit(5).all()

        top_users = [
            {"user_id": u[0], "requests": u[1], "cost_usd": round(u[2], 4)}
            for u in user_stats
        ]

        # Violations
        violations = self.db.query(func.count(AuditViolation.id)).filter(
            AuditViolation.timestamp >= cutoff,
        ).scalar() or 0

        avg_cost = total_cost / total_requests if total_requests > 0 else 0

        return SummaryStats(
            total_requests=total_requests,
            total_cost_usd=round(total_cost, 4),
            total_tokens=total_tokens,
            requests_by_model=requests_by_model,
            cost_by_model=cost_by_model,
            top_users=top_users,
            violations=violations,
            average_cost_per_request=round(avg_cost, 6),
        )

    def get_request_decrypted(self, request_id: int) -> dict | None:
        """Return a single audit record with prompt/response decrypted. Compliance use only."""
        r = self.db.query(AuditRequest).filter(AuditRequest.id == request_id).first()
        if not r:
            return None
        return {
            "id": r.id,
            "timestamp": r.timestamp,
            "user_id": r.user_id,
            "prompt": decrypt_field(r.prompt),
            "response": decrypt_field(r.response),
            "model_used": r.model_used,
            "tokens_in": r.tokens_in,
            "tokens_out": r.tokens_out,
            "cost_usd": r.cost_usd,
            "policy_decision": r.policy_decision,
            "duration_ms": r.duration_ms,
            "error_message": r.error_message,
        }

    def get_violations(self, hours: int = 24) -> list:
        """Get recent policy violations."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        violations = self.db.query(AuditViolation).filter(
            AuditViolation.timestamp >= cutoff,
        ).order_by(AuditViolation.timestamp.desc()).all()

        return [
            {
                "timestamp": v.timestamp,
                "user_id": v.user_id,
                "reason": v.violation_reason,
                "details": v.details,
            }
            for v in violations
        ]

    def get_decisions_summary(self, hours: int = 24) -> dict:
        """Get policy decision breakdown for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        total = self.db.query(func.count(AuditRequest.id)).filter(
            AuditRequest.timestamp >= cutoff
        ).scalar() or 0

        approved = self.db.query(func.count(AuditRequest.id)).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision == "approved"
        ).scalar() or 0

        rejected = total - approved

        violations = self.db.query(AuditRequest.policy_decision, func.count(AuditRequest.id)).filter(
            AuditRequest.timestamp >= cutoff,
            AuditRequest.policy_decision != "approved"
        ).group_by(AuditRequest.policy_decision).all()

        violation_breakdown = {}
        for decision, count in violations:
            if decision:
                violation_breakdown[decision] = count

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "violations": violation_breakdown,
        }
