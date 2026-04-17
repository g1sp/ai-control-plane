"""Tool execution approval workflow."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy.orm import Session

from ..database import ToolApproval


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ToolApprovalRequest:
    """Represents a tool approval request."""

    def __init__(
        self,
        approval_id: str,
        user_id: str,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ):
        self.approval_id = approval_id
        self.user_id = user_id
        self.tool_name = tool_name
        self.args = args or {}
        self.created_at = created_at or datetime.utcnow()


class ToolApprovalEngine:
    """Manage tool execution approvals."""

    # Tools that require approval by default
    DEFAULT_APPROVAL_REQUIRED = {"python_eval", "sql_query", "sql_execute"}

    def __init__(self, db: Session):
        self.db = db

    def should_require_approval(self, tool_name: str, user_id: str) -> bool:
        """Check if tool execution requires approval.

        Args:
            tool_name: Name of tool
            user_id: User requesting tool

        Returns:
            True if approval required
        """
        # Check if tool is in default approval list
        if tool_name in self.DEFAULT_APPROVAL_REQUIRED:
            return True

        # Could extend this to check per-user policies
        return False

    def request_approval(
        self,
        user_id: str,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> ToolApprovalRequest:
        """Request tool execution approval.

        Args:
            user_id: User requesting tool
            tool_name: Tool to execute
            args: Tool arguments

        Returns:
            ToolApprovalRequest with status pending
        """
        approval_id = f"approval_{uuid.uuid4().hex[:12]}"

        # Store in database
        approval_record = ToolApproval(
            user_id=user_id,
            tool_name=tool_name,
            args=args,
            status=ApprovalStatus.PENDING.value,
        )
        self.db.add(approval_record)
        self.db.commit()

        return ToolApprovalRequest(
            approval_id=approval_id,
            user_id=user_id,
            tool_name=tool_name,
            args=args,
        )

    def get_approval_status(self, approval_id: str) -> Optional[ApprovalStatus]:
        """Get approval status.

        Args:
            approval_id: Approval ID

        Returns:
            Approval status or None if not found
        """
        # In production, lookup by ID in database
        # For now, assume ID format stores state
        return None

    def approve(self, approval_id: str, approved_by: str) -> bool:
        """Approve a tool request.

        Args:
            approval_id: Approval ID
            approved_by: Admin user ID

        Returns:
            True if approved successfully
        """
        # Update database
        approval = self.db.query(ToolApproval).filter_by(
            # ... lookup logic
        ).first()

        if not approval:
            return False

        approval.status = ApprovalStatus.APPROVED.value
        approval.decided_at = datetime.utcnow()
        approval.decision_by = approved_by
        self.db.commit()

        return True

    def reject(self, approval_id: str, rejected_by: str) -> bool:
        """Reject a tool request.

        Args:
            approval_id: Approval ID
            rejected_by: Admin user ID

        Returns:
            True if rejected successfully
        """
        # Update database
        approval = self.db.query(ToolApproval).filter_by(
            # ... lookup logic
        ).first()

        if not approval:
            return False

        approval.status = ApprovalStatus.REJECTED.value
        approval.decided_at = datetime.utcnow()
        approval.decision_by = rejected_by
        self.db.commit()

        return True

    def get_pending_approvals(self, limit: int = 50) -> list:
        """Get pending approval requests.

        Args:
            limit: Max results

        Returns:
            List of pending ToolApprovalRequest objects
        """
        pending = self.db.query(ToolApproval).filter_by(
            status=ApprovalStatus.PENDING.value
        ).limit(limit).all()

        return [
            ToolApprovalRequest(
                approval_id=str(p.id),
                user_id=p.user_id,
                tool_name=p.tool_name,
                args=p.args,
                created_at=p.created_at,
            )
            for p in pending
        ]

    def get_user_approvals(self, user_id: str, status: Optional[str] = None) -> list:
        """Get approvals for a user.

        Args:
            user_id: User ID
            status: Filter by status

        Returns:
            List of ToolApprovalRequest objects
        """
        query = self.db.query(ToolApproval).filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        approvals = query.all()

        return [
            ToolApprovalRequest(
                approval_id=str(a.id),
                user_id=a.user_id,
                tool_name=a.tool_name,
                args=a.args,
                created_at=a.created_at,
            )
            for a in approvals
        ]
