"""Policy enforcement engine."""

import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..config import settings
from ..models import PolicyDecisionEnum, PolicyDecision, QueryRequest
from ..database import AuditViolation


class PolicyEngine:
    """Evaluate policy decisions for requests."""

    def __init__(self, db: Session = None):
        self.db = db
        # In-memory rate limit tracking (user_id -> (count, timestamp))
        self.rate_limits = {}

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

        # Check 2: Injection detection
        if self.check_injection(request.prompt):
            reason = "injection_detected"
            self._log_violation(request.user_id, reason, "Prompt injection pattern detected")
            return PolicyDecision(approved=False, reason=reason)

        # Check 3: Model whitelist
        if request.model != "auto" and request.model not in settings.models_whitelist:
            reason = "model_not_whitelisted"
            self._log_violation(request.user_id, reason, f"Model {request.model} not whitelisted")
            return PolicyDecision(approved=False, reason=reason)

        # Check 4: Rate limit
        if not self.check_rate_limit(request.user_id):
            reason = "rate_limited"
            until = datetime.utcnow() + timedelta(minutes=1)
            return PolicyDecision(approved=False, reason=reason, rate_limited_until=until)

        # Check 5: Budget (we'll do preliminary check, but verify after cost calculation)
        if request.budget_usd > settings.budget_per_request_usd:
            reason = "budget_exceeded"
            self._log_violation(
                request.user_id,
                reason,
                f"Budget ${request.budget_usd} exceeds limit ${settings.budget_per_request_usd}",
            )
            return PolicyDecision(approved=False, reason=reason)

        # All checks passed
        return PolicyDecision(approved=True, reason="approved")

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
