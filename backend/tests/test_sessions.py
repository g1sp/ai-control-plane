"""Tests for agent session management."""

import pytest
from datetime import datetime, timedelta
from src.agents.session import (
    ConversationMessage, SessionContext, AgentSession, SessionManager,
    SessionStatus, get_session_manager
)


class TestConversationMessage:
    """Test conversation messages."""

    def test_create_message(self):
        """Test creating a message."""
        msg = ConversationMessage(
            role="user",
            content="What is the capital of France?",
            timestamp=datetime.utcnow(),
            tokens_used=10,
            cost_usd=0.001
        )

        assert msg.role == "user"
        assert msg.content == "What is the capital of France?"
        assert msg.tokens_used == 10
        assert msg.cost_usd == 0.001

    def test_message_to_dict(self):
        """Test message serialization."""
        msg = ConversationMessage(
            role="assistant",
            content="Paris is the capital of France.",
            timestamp=datetime(2026, 4, 16, 12, 0, 0),
            tokens_used=5,
            cost_usd=0.0005
        )

        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Paris is the capital of France."
        assert "2026-04-16" in data["timestamp"]


class TestSessionContext:
    """Test session context."""

    def test_create_context(self):
        """Test creating session context."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test-session",
            goal="Learn about France",
            budget_usd=1.0
        )

        assert ctx.user_id == "user@example.com"
        assert ctx.goal == "Learn about France"
        assert ctx.budget_usd == 1.0
        assert ctx.spent_usd == 0.0
        assert len(ctx.messages) == 0

    def test_add_message(self):
        """Test adding message to context."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=1.0
        )

        msg = ctx.add_message("user", "Hello", tokens=5, cost=0.0005)

        assert len(ctx.messages) == 1
        assert ctx.spent_usd == 0.0005
        assert msg.role == "user"

    def test_record_tool_use(self):
        """Test recording tool usage."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=1.0
        )

        ctx.record_tool_use("search", {"query": "France"}, "Found: ...")

        assert len(ctx.tool_history) == 1
        assert ctx.tool_history[0]["tool"] == "search"

    def test_get_remaining_budget(self):
        """Test budget tracking."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=1.0
        )

        assert ctx.get_remaining_budget() == 1.0

        ctx.spent_usd = 0.3
        assert ctx.get_remaining_budget() == 0.7

        ctx.spent_usd = 1.5  # Over budget
        assert ctx.get_remaining_budget() == 0.0

    def test_is_over_budget(self):
        """Test budget overflow detection."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=1.0
        )

        assert not ctx.is_over_budget()

        ctx.spent_usd = 1.0
        assert ctx.is_over_budget()

    def test_is_expired(self):
        """Test session expiration."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=1.0,
            ttl_seconds=1
        )

        assert not ctx.is_expired()

        # Manually set created_at to past
        ctx.created_at = datetime.utcnow() - timedelta(seconds=2)
        assert ctx.is_expired()

    def test_get_conversation_summary(self):
        """Test conversation summary generation."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Learn about capitals",
            budget_usd=1.0
        )

        ctx.add_message("user", "What is the capital of France?")
        ctx.add_message("assistant", "Paris")
        ctx.record_tool_use("search", {}, "Found info")

        summary = ctx.get_conversation_summary()
        assert "Learn about capitals" in summary
        assert "Paris" in summary
        assert "search" in summary

    def test_context_to_dict(self):
        """Test context serialization."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=1.0
        )

        ctx.add_message("user", "Hello")
        data = ctx.to_dict()

        assert data["user_id"] == "user@example.com"
        assert len(data["messages"]) == 1
        assert data["spent_usd"] == 0.0


class TestAgentSession:
    """Test agent sessions."""

    def test_create_session(self):
        """Test creating agent session."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test goal"
        )

        assert session.user_id == "user@example.com"
        assert session.goal == "Test goal"
        assert session.status == SessionStatus.ACTIVE
        assert session.completed_turns == 0
        assert session.context is not None

    def test_session_with_context(self):
        """Test session with custom context."""
        ctx = SessionContext(
            user_id="user@example.com",
            session_id="test",
            goal="Test",
            budget_usd=2.0
        )

        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test",
            context=ctx
        )

        assert session.context.budget_usd == 2.0

    def test_start_turn(self):
        """Test starting conversation turn."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test"
        )

        assert session.start_turn() is True
        assert session.is_active() is True

    def test_turn_limits(self):
        """Test max turn enforcement."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test",
            max_turns=3
        )

        assert session.start_turn() is True
        session.end_turn()
        assert session.completed_turns == 1

        assert session.start_turn() is True
        session.end_turn()
        assert session.completed_turns == 2

        assert session.start_turn() is True
        session.end_turn()
        assert session.completed_turns == 3

        # Should fail on 4th turn
        assert session.start_turn() is False
        assert session.status == SessionStatus.COMPLETED

    def test_pause_resume(self):
        """Test pausing and resuming session."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test"
        )

        assert session.status == SessionStatus.ACTIVE

        session.pause()
        assert session.status == SessionStatus.PAUSED

        assert session.resume() is True
        assert session.status == SessionStatus.ACTIVE

    def test_terminate(self):
        """Test terminating session."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test"
        )

        session.terminate("User quit")
        assert session.status == SessionStatus.TERMINATED

    def test_session_to_dict(self):
        """Test session serialization."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test"
        )

        data = session.to_dict()
        assert data["session_id"] == "test"
        assert data["status"] == "active"
        assert data["completed_turns"] == 0


class TestSessionManager:
    """Test session manager."""

    def test_create_session(self):
        """Test creating session via manager."""
        manager = SessionManager()
        session_id = manager.create_session("user@example.com", "Test goal", 1.0)

        assert session_id is not None
        session = manager.get_session(session_id)
        assert session is not None
        assert session.user_id == "user@example.com"

    def test_get_nonexistent_session(self):
        """Test getting non-existent session."""
        manager = SessionManager()
        session = manager.get_session("nonexistent")
        assert session is None

    def test_list_user_sessions(self):
        """Test listing user's sessions."""
        manager = SessionManager()

        session_id1 = manager.create_session("user1@example.com", "Goal 1")
        session_id2 = manager.create_session("user1@example.com", "Goal 2")
        session_id3 = manager.create_session("user2@example.com", "Goal 3")

        user1_sessions = manager.list_user_sessions("user1@example.com")
        assert len(user1_sessions) == 2

        user2_sessions = manager.list_user_sessions("user2@example.com")
        assert len(user2_sessions) == 1

    def test_pause_session(self):
        """Test pausing session via manager."""
        manager = SessionManager()
        session_id = manager.create_session("user@example.com", "Test")

        assert manager.pause_session(session_id) is True

        session = manager.get_session(session_id)
        assert session.status == SessionStatus.PAUSED

    def test_resume_session(self):
        """Test resuming session via manager."""
        manager = SessionManager()
        session_id = manager.create_session("user@example.com", "Test")

        manager.pause_session(session_id)
        assert manager.resume_session(session_id) is True

        session = manager.get_session(session_id)
        assert session.status == SessionStatus.ACTIVE

    def test_terminate_session(self):
        """Test terminating session via manager."""
        manager = SessionManager()
        session_id = manager.create_session("user@example.com", "Test")

        assert manager.terminate_session(session_id, "Test termination") is True

        session = manager.get_session(session_id)
        assert session.status == SessionStatus.TERMINATED

    def test_cleanup_expired(self):
        """Test cleaning up expired sessions."""
        manager = SessionManager(ttl_seconds=1)

        session_id = manager.create_session("user@example.com", "Test")
        session = manager.get_session(session_id)
        session.context.created_at = datetime.utcnow() - timedelta(seconds=2)

        cleaned = manager.cleanup_expired()
        assert cleaned == 1
        assert manager.get_session(session_id) is None

    def test_get_stats(self):
        """Test getting session statistics."""
        manager = SessionManager()

        session_id1 = manager.create_session("user@example.com", "Goal 1")
        session_id2 = manager.create_session("user@example.com", "Goal 2")

        manager.pause_session(session_id2)

        stats = manager.get_stats()
        assert stats["total_sessions"] == 2
        assert stats["active"] == 1
        assert stats["paused"] == 1


class TestMultiTurnConversation:
    """Test multi-turn conversation scenarios."""

    def test_multi_turn_conversation(self):
        """Test complete multi-turn conversation."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Learn about geography"
        )

        # Turn 1
        assert session.start_turn() is True
        session.context.add_message("user", "What is the capital of France?", tokens=10, cost=0.001)
        session.context.add_message("assistant", "Paris", tokens=5, cost=0.0005)
        session.end_turn()
        assert session.completed_turns == 1

        # Turn 2
        assert session.start_turn() is True
        session.context.add_message("user", "What is the capital of Germany?", tokens=10, cost=0.001)
        session.context.add_message("assistant", "Berlin", tokens=5, cost=0.0005)
        session.end_turn()
        assert session.completed_turns == 2

        # Verify history is preserved
        assert len(session.context.messages) == 4
        assert abs(session.context.spent_usd - 0.003) < 0.0001  # Account for float precision

    def test_conversation_with_tool_calls(self):
        """Test conversation with tool usage tracking."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Research task"
        )

        session.start_turn()

        session.context.add_message("user", "Search for climate change info")
        session.context.record_tool_use("search", {"query": "climate change"}, "Found 1000 results")
        session.context.add_message("assistant", "I found information about climate change")

        session.end_turn()

        assert len(session.context.tool_history) == 1
        assert session.context.tool_history[0]["tool"] == "search"

    def test_session_memory_context(self):
        """Test that agent receives conversation context."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Multi-turn Q&A"
        )

        session.context.add_message("user", "Tell me about Paris")
        session.context.add_message("assistant", "Paris is the capital of France")
        session.context.add_message("user", "And what about Berlin?")

        summary = session.context.get_conversation_summary()

        # Summary should contain topic and recent messages
        assert "Multi-turn Q&A" in summary
        assert "Berlin" in summary or "Paris" in summary


class TestSessionIntegration:
    """Integration tests for sessions."""

    def test_session_lifecycle(self):
        """Test complete session lifecycle."""
        manager = SessionManager(ttl_seconds=3600)

        # Create
        session_id = manager.create_session("user@example.com", "Interesting topic", 5.0)
        session = manager.get_session(session_id)
        assert session.status == SessionStatus.ACTIVE

        # Use for multiple turns
        for i in range(3):
            assert session.start_turn() is True
            session.context.add_message("user", f"Question {i}")
            session.context.add_message("assistant", f"Answer {i}")
            session.end_turn()

        assert session.completed_turns == 3

        # Pause
        session.pause()
        assert session.status == SessionStatus.PAUSED

        # Resume
        session.resume()
        assert session.status == SessionStatus.ACTIVE

        # Continue with more turns
        assert session.start_turn() is True
        session.end_turn()
        assert session.completed_turns == 4

        # Terminate
        session.terminate("Complete")
        assert session.status == SessionStatus.TERMINATED

    def test_budget_enforcement_across_turns(self):
        """Test budget tracking across multiple turns."""
        session = AgentSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test"
        )
        session.context.budget_usd = 0.1

        # Turn 1: Use half budget
        assert session.start_turn() is True
        session.context.add_message("user", "Hello", tokens=50, cost=0.05)
        session.context.add_message("assistant", "Hi", tokens=5, cost=0.0)
        session.end_turn()

        assert abs(session.context.get_remaining_budget() - 0.05) < 0.001
        assert not session.context.is_over_budget()

        # Turn 2: Use remaining
        assert session.start_turn() is True
        session.context.add_message("user", "More", tokens=50, cost=0.06)  # Over budget
        session.end_turn()

        # Turn 3: Should fail due to budget
        assert session.context.is_over_budget()
        assert session.start_turn() is False  # Should fail


class TestGlobalSessionManager:
    """Test global session manager."""

    def test_get_session_manager(self):
        """Test getting global manager."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        assert manager1 is manager2
