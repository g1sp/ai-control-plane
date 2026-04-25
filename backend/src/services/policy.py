"""Policy enforcement engine."""

import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..config import settings
from ..models import PolicyDecisionEnum, PolicyDecision, QueryRequest
from ..database import AuditViolation
from .policy_dsl import get_policy_engine, PolicyAction
from ..ml.threat_detector import get_threat_detector, ThreatCategory
from .redis_rate_limiter import get_rate_limiter


class PolicyEngine:
    """Evaluate policy decisions for requests."""

    def __init__(self, db: Session = None):
        self.db = db
        self.rate_limits = {}  # kept for _get_requests_last_minute tracking
        self._dsl = get_policy_engine()
        self._threat = get_threat_detector()
        self._rate_limiter = get_rate_limiter()

    def evaluate(self, request: QueryRequest) -> PolicyDecision:
        """
        Evaluate if request is approved based on all policies.

        Returns: PolicyDecision with approved: bool and reason: str
        """
        # Check 1: User whitelist
        if request.user_id not in settings.users_whitelist:
            reason = "user_not_whitelisted"
            self._log_violation(request.user_id, reason, f"User {request.user_id} not in whitelist")
            return PolicyDecision(approved=False, reason=reason)

        # Check 2: ML threat detection
        threat = self._threat.score(request.prompt)
        if threat.score >= self._threat.block_threshold:
            reason = f"ml_threat_detected:{threat.category}"
            self._log_violation(request.user_id, reason, f"Threat score {threat.score:.2f} category={threat.category}")
            return PolicyDecision(approved=False, reason=reason)

        # Check 3: DSL input policies — receives ml threat score so YAML rules can reference it
        dsl_result = self._dsl.first_block_or_escalate("input", {
            "prompt": request.prompt,
            "user_id": request.user_id,
            "risk_score": threat.score,
            "threat_category": threat.category,
        })
        if dsl_result and dsl_result.action == PolicyAction.BLOCK:
            self._log_violation(request.user_id, dsl_result.rule_name, dsl_result.message)
            return PolicyDecision(approved=False, reason=dsl_result.rule_name)

        # Check 3: Legacy regex injection (kept as fallback)
        if self.check_injection(request.prompt):
            reason = "injection_detected"
            self._log_violation(request.user_id, reason, "Prompt injection pattern detected")
            return PolicyDecision(approved=False, reason=reason)

        # Check 4: Model whitelist
        if request.model != "auto" and request.model not in settings.models_whitelist:
            reason = "model_not_whitelisted"
            self._log_violation(request.user_id, reason, f"Model {request.model} not whitelisted")
            return PolicyDecision(approved=False, reason=reason)

        # Check 5: Rate limit (Redis-backed sliding window, falls back to memory)
        allowed, rate_info = self._rate_limiter.check(request.user_id, "per_minute")
        if not allowed:
            reason = "rate_limited"
            until = datetime.utcnow() + timedelta(minutes=1)
            return PolicyDecision(approved=False, reason=reason, rate_limited_until=until)

        # Check 6: Budget (preliminary check, verified again after cost calculation)
        if request.budget_usd > settings.budget_per_request_usd:
            reason = "budget_exceeded"
            self._log_violation(
                request.user_id,
                reason,
                f"Budget ${request.budget_usd} exceeds limit ${settings.budget_per_request_usd}",
            )
            return PolicyDecision(approved=False, reason=reason)

        # Check 7: DSL pre-execution policies (cost/rate escalation rules)
        requests_last_minute = self._get_requests_last_minute(request.user_id)
        dsl_pre = self._dsl.first_block_or_escalate("pre_execution", {
            "prompt": request.prompt,
            "user_id": request.user_id,
            "estimated_cost": request.budget_usd,
            "requests_last_minute": requests_last_minute,
        })
        if dsl_pre:
            if dsl_pre.action == PolicyAction.BLOCK:
                self._log_violation(request.user_id, dsl_pre.rule_name, dsl_pre.message)
                return PolicyDecision(approved=False, reason=dsl_pre.rule_name)
            if dsl_pre.action == PolicyAction.ESCALATE:
                self._log_violation(request.user_id, dsl_pre.rule_name, dsl_pre.message)
                return PolicyDecision(approved=False, reason=f"escalation_required:{dsl_pre.rule_name}")

        return PolicyDecision(approved=True, reason="approved")

    def evaluate_tool_call(self, user_id: str, tool: str, args: dict, risk_score: float = 0.0) -> PolicyDecision:
        """Evaluate a tool call against DSL tool_call policies."""
        # Score the serialized args through the threat detector for indirect injection
        args_text = " ".join(str(v) for v in args.values()) if args else ""
        if args_text:
            threat = self._threat.score(args_text)
            risk_score = max(risk_score, threat.score)

        result = self._dsl.first_block_or_escalate("tool_call", {
            "tool": tool,
            "args": args,
            "risk_score": risk_score,
            "user_id": user_id,
        })
        if result is None:
            return PolicyDecision(approved=True, reason="approved")
        if result.action == PolicyAction.BLOCK:
            self._log_violation(user_id, result.rule_name, result.message)
            return PolicyDecision(approved=False, reason=result.rule_name)
        if result.action == PolicyAction.ESCALATE:
            self._log_violation(user_id, result.rule_name, result.message)
            return PolicyDecision(approved=False, reason=f"escalation_required:{result.rule_name}")
        return PolicyDecision(approved=True, reason="approved")

    def _get_requests_last_minute(self, user_id: str) -> int:
        if user_id not in self.rate_limits:
            return 0
        count, timestamp = self.rate_limits[user_id]
        if (datetime.utcnow() - timestamp).total_seconds() > 60:
            return 0
        return count

    def check_injection(self, prompt: str) -> bool:
        """Check if prompt contains injection patterns."""
        prompt_lower = prompt.lower()
        for pattern in settings.injection_patterns:
            if re.search(rf"\b{re.escape(pattern)}\b", prompt_lower, re.IGNORECASE):
                return True
        return False

    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit (requests per minute)."""
        now = datetime.utcnow()

        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = (1, now)
            return True

        count, timestamp = self.rate_limits[user_id]

        # If more than 1 minute has passed, reset
        if (now - timestamp).total_seconds() > 60:
            self.rate_limits[user_id] = (1, now)
            return True

        # Within same minute window
        if count >= settings.rate_limit_req_per_minute:
            return False

        self.rate_limits[user_id] = (count + 1, timestamp)
        return True

    def check_model_allowed(self, model: str) -> bool:
        """Check if model is whitelisted."""
        return model in settings.models_whitelist

    def _log_violation(self, user_id: str, reason: str, details: str):
        """Log policy violation to database."""
        if self.db:
            violation = AuditViolation(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                violation_reason=reason,
                details=details,
            )
            self.db.add(violation)
            self.db.commit()
