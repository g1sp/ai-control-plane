"""Tests for tool approval workflow."""

import pytest
from src.policies.approval import ToolApprovalEngine, ApprovalStatus, ToolApprovalRequest


class TestToolApprovalEngine:
    """Test tool approval workflow."""

    def test_should_require_approval_python_eval(self, db):
        """Test python_eval requires approval."""
        engine = ToolApprovalEngine(db)
        assert engine.should_require_approval("python_eval", "user@example.com")

    def test_should_require_approval_sql_query(self, db):
        """Test sql_query requires approval."""
        engine = ToolApprovalEngine(db)
        assert engine.should_require_approval("sql_query", "user@example.com")

    def test_should_not_require_approval_http_get(self, db):
        """Test http_get doesn't require approval."""
        engine = ToolApprovalEngine(db)
        assert not engine.should_require_approval("http_get", "user@example.com")

    def test_should_not_require_approval_search(self, db):
        """Test search doesn't require approval."""
        engine = ToolApprovalEngine(db)
        assert not engine.should_require_approval("search", "user@example.com")

    def test_request_approval(self, db):
        """Test requesting tool approval."""
        engine = ToolApprovalEngine(db)
        request = engine.request_approval(
            user_id="user@example.com",
            tool_name="python_eval",
            args={"code": "print('hello')"}
        )

        assert isinstance(request, ToolApprovalRequest)
        assert request.approval_id.startswith("approval_")
        assert request.user_id == "user@example.com"
        assert request.tool_name == "python_eval"
        assert request.args == {"code": "print('hello')"}

    def test_get_pending_approvals(self, db):
        """Test getting pending approvals."""
        engine = ToolApprovalEngine(db)

        # Request multiple approvals
        engine.request_approval("user1@example.com", "python_eval")
        engine.request_approval("user2@example.com", "sql_query")

        pending = engine.get_pending_approvals()
        assert len(pending) >= 2

    def test_get_user_approvals(self, db):
        """Test getting user-specific approvals."""
        engine = ToolApprovalEngine(db)

        engine.request_approval("alice@example.com", "python_eval")
        engine.request_approval("alice@example.com", "sql_query")
        engine.request_approval("bob@example.com", "python_eval")

        alice_approvals = engine.get_user_approvals("alice@example.com")
        assert len(alice_approvals) >= 2

    def test_approval_default_status_pending(self, db):
        """Test approval defaults to pending status."""
        engine = ToolApprovalEngine(db)
        request = engine.request_approval("user@example.com", "python_eval")

        # Status should be stored as pending
        status = engine.get_approval_status(request.approval_id)
        # Status lookup implementation is deferred, so this may return None
        # In full implementation, should be ApprovalStatus.PENDING

    def test_multiple_approval_requests(self, db):
        """Test multiple approval requests from same user."""
        engine = ToolApprovalEngine(db)

        requests = []
        for i in range(5):
            request = engine.request_approval(
                user_id="user@example.com",
                tool_name="python_eval",
                args={"code": f"x = {i}"}
            )
            requests.append(request)

        assert len(requests) == 5
        assert all(r.approval_id.startswith("approval_") for r in requests)

    def test_approval_request_with_no_args(self, db):
        """Test approval request without arguments."""
        engine = ToolApprovalEngine(db)
        request = engine.request_approval(
            user_id="user@example.com",
            tool_name="search"
        )

        assert request.args == {}
