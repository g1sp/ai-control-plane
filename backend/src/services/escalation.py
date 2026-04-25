"""
Escalation service for human-in-the-loop review of high-risk agent actions.

Handles policy-triggered escalations (from policy_dsl ESCALATE rules) and
tool approval requests. Persists to the existing ToolApproval table.

Timeout behavior is configurable:
  ESCALATION_TIMEOUT_SECONDS  (default: 300)
  ESCALATION_TIMEOUT_ACTION   "deny" (fail-safe) | "approve" (fail-open)
"""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..database import ToolApproval


class EscalationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMED_OUT = "timed_out"


@dataclass
class EscalationItem:
    id: str
    user_id: str
    trigger_type: str           # "policy_rule" | "tool_call"
    trigger_name: str           # rule name or tool name
    context: dict[str, Any]     # full context for the reviewer
    risk_score: float
    policy_message: str
    status: EscalationStatus
    created_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    comment: Optional[str] = None

    def is_timed_out(self) -> bool:
        timeout_seconds = int(os.environ.get("ESCALATION_TIMEOUT_SECONDS", "300"))
        return (
            self.status == EscalationStatus.PENDING
            and (datetime.utcnow() - self.created_at).total_seconds() > timeout_seconds
        )

    def timeout_action(self) -> EscalationStatus:
        action = os.environ.get("ESCALATION_TIMEOUT_ACTION", "deny").lower()
        return EscalationStatus.APPROVED if action == "approve" else EscalationStatus.DENIED


class EscalationService:
    """Create, query, and decide escalation items."""

    def __init__(self, db: Session):
        self._db = db

    def create(
        self,
        user_id: str,
        trigger_type: str,
        trigger_name: str,
        context: dict[str, Any],
        risk_score: float,
        policy_message: str,
    ) -> EscalationItem:
        record = ToolApproval(
            user_id=user_id,
            tool_name=f"{trigger_type}:{trigger_name}",
            args={
                "context": context,
                "risk_score": risk_score,
                "policy_message": policy_message,
                "trigger_type": trigger_type,
                "trigger_name": trigger_name,
            },
            status=EscalationStatus.PENDING.value,
            created_at=datetime.utcnow(),
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return self._to_item(record)

    def get(self, escalation_id: int) -> Optional[EscalationItem]:
        record = self._db.query(ToolApproval).filter(ToolApproval.id == escalation_id).first()
        if not record:
            return None
        item = self._to_item(record)
        # Check timeout lazily at read time
        if item.is_timed_out():
            self._apply_timeout(record, item)
            item.status = item.timeout_action()
        return item

    def decide(self, escalation_id: int, approved: bool, decided_by: str, comment: str = "") -> Optional[EscalationItem]:
        record = self._db.query(ToolApproval).filter(ToolApproval.id == escalation_id).first()
        if not record or record.status != EscalationStatus.PENDING.value:
            return None
        record.status = EscalationStatus.APPROVED.value if approved else EscalationStatus.DENIED.value
        record.decided_at = datetime.utcnow()
        record.decision_by = decided_by
        if record.args is None:
            record.args = {}
        record.args["comment"] = comment
        self._db.commit()
        self._db.refresh(record)
        return self._to_item(record)

    def list_pending(self, limit: int = 50) -> list[EscalationItem]:
        records = (
            self._db.query(ToolApproval)
            .filter(ToolApproval.status == EscalationStatus.PENDING.value)
            .order_by(ToolApproval.created_at.asc())
            .limit(limit)
            .all()
        )
        items = []
        for r in records:
            item = self._to_item(r)
            if item.is_timed_out():
                self._apply_timeout(r, item)
                item.status = item.timeout_action()
            else:
                items.append(item)
        return items

    def list_all(self, limit: int = 100, offset: int = 0) -> list[EscalationItem]:
        records = (
            self._db.query(ToolApproval)
            .order_by(ToolApproval.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_item(r) for r in records]

    def _apply_timeout(self, record: ToolApproval, item: EscalationItem) -> None:
        new_status = item.timeout_action()
        record.status = new_status.value
        record.decided_at = datetime.utcnow()
        record.decision_by = "system:timeout"
        self._db.commit()

    def _to_item(self, r: ToolApproval) -> EscalationItem:
        args = r.args or {}
        return EscalationItem(
            id=str(r.id),
            user_id=r.user_id,
            trigger_type=args.get("trigger_type", "tool_call"),
            trigger_name=args.get("trigger_name", r.tool_name),
            context=args.get("context", {}),
            risk_score=args.get("risk_score", 0.0),
            policy_message=args.get("policy_message", ""),
            status=EscalationStatus(r.status),
            created_at=r.created_at,
            decided_at=r.decided_at,
            decided_by=r.decision_by,
            comment=args.get("comment"),
        )
