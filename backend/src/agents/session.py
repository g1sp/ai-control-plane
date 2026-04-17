"""Agent session management for multi-turn conversations."""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum


class SessionStatus(str, Enum):
    """Session lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class ConversationMessage:
    """Single message in conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    tokens_used: int = 0
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
        }


@dataclass
class SessionContext:
    """Context preserved across conversation turns."""
    user_id: str
    session_id: str
    goal: str  # Original goal/topic
    budget_usd: float
    spent_usd: float = 0.0
    messages: List[ConversationMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Custom user data
    tool_history: List[Dict[str, Any]] = field(default_factory=list)  # Tools used
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 3600  # 1 hour default

    def add_message(self, role: str, content: str, tokens: int = 0, cost: float = 0.0) -> ConversationMessage:
        """Add message to conversation."""
        msg = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            tokens_used=tokens,
            cost_usd=cost,
        )
        self.messages.append(msg)
        self.spent_usd += cost
        self.updated_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        return msg

    def record_tool_use(self, tool_name: str, args: Dict[str, Any], result: str) -> None:
        """Record tool usage in session."""
        self.tool_history.append({
            "tool": tool_name,
            "args": args,
            "result": result[:500],  # Limit result size
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.updated_at = datetime.utcnow()

    def get_conversation_summary(self) -> str:
        """Get summary of conversation for agent context."""
        lines = [f"Topic: {self.goal}", f"Spent: ${self.spent_usd:.4f} / ${self.budget_usd}"]

        if self.messages:
            lines.append("\nRecent conversation:")
            for msg in self.messages[-5:]:  # Last 5 messages
                lines.append(f"  {msg.role.upper()}: {msg.content[:100]}")

        if self.tool_history:
            lines.append("\nTools used:")
            for tool in self.tool_history[-3:]:  # Last 3 tools
                lines.append(f"  - {tool['tool']}")

        return "\n".join(lines)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        age = datetime.utcnow() - self.created_at
        return age.total_seconds() > self.ttl_seconds

    def is_over_budget(self) -> bool:
        """Check if session exceeded budget."""
        return self.spent_usd >= self.budget_usd

    def get_remaining_budget(self) -> float:
        """Get remaining budget for session."""
        return max(0, self.budget_usd - self.spent_usd)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "goal": self.goal,
            "budget_usd": self.budget_usd,
            "spent_usd": self.spent_usd,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
            "tool_history": self.tool_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }


@dataclass
class AgentSession:
    """Complete agent session with state."""
    session_id: str
    user_id: str
    goal: str
    status: SessionStatus = SessionStatus.ACTIVE
    context: Optional[SessionContext] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_turns: int = 0
    max_turns: int = 20

    def __post_init__(self):
        """Initialize context if not provided."""
        if self.context is None:
            self.context = SessionContext(
                user_id=self.user_id,
                session_id=self.session_id,
                goal=self.goal,
                budget_usd=1.0,  # Default budget
            )

    def start_turn(self) -> bool:
        """Start new conversation turn."""
        if self.status != SessionStatus.ACTIVE:
            return False

        if self.completed_turns >= self.max_turns:
            self.status = SessionStatus.COMPLETED
            return False

        if self.context.is_expired():
            self.status = SessionStatus.EXPIRED
            return False

        if self.context.is_over_budget():
            self.status = SessionStatus.COMPLETED
            return False

        return True

    def end_turn(self) -> None:
        """End conversation turn."""
        self.completed_turns += 1
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause session."""
        if self.status == SessionStatus.ACTIVE:
            self.status = SessionStatus.PAUSED
            self.updated_at = datetime.utcnow()

    def resume(self) -> bool:
        """Resume paused session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
            self.updated_at = datetime.utcnow()
            return True
        return False

    def terminate(self, reason: str = "User terminated") -> None:
        """Terminate session."""
        self.status = SessionStatus.TERMINATED
        self.context.add_message("system", f"Session terminated: {reason}")
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE and not self.context.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "goal": self.goal,
            "status": self.status.value,
            "context": self.context.to_dict() if self.context else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_turns": self.completed_turns,
            "max_turns": self.max_turns,
        }


class SessionManager:
    """Manages agent sessions and their lifecycle."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize session manager."""
        self.sessions: Dict[str, AgentSession] = {}
        self.ttl_seconds = ttl_seconds

    def create_session(self, user_id: str, goal: str, budget_usd: float = 1.0) -> str:
        """Create new session."""
        session_id = str(uuid.uuid4())
        session = AgentSession(
            session_id=session_id,
            user_id=user_id,
            goal=goal,
        )
        session.context.budget_usd = budget_usd
        session.context.ttl_seconds = self.ttl_seconds
        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get session by ID."""
        session = self.sessions.get(session_id)
        if session and session.context.is_expired():
            session.status = SessionStatus.EXPIRED
        return session

    def list_user_sessions(self, user_id: str) -> List[AgentSession]:
        """List all sessions for user."""
        return [s for s in self.sessions.values() if s.user_id == user_id]

    def pause_session(self, session_id: str) -> bool:
        """Pause session."""
        session = self.get_session(session_id)
        if session:
            session.pause()
            return True
        return False

    def resume_session(self, session_id: str) -> bool:
        """Resume session."""
        session = self.get_session(session_id)
        if session:
            return session.resume()
        return False

    def terminate_session(self, session_id: str, reason: str = "User terminated") -> bool:
        """Terminate session."""
        session = self.get_session(session_id)
        if session:
            session.terminate(reason)
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.context.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active = sum(1 for s in self.sessions.values() if s.status == SessionStatus.ACTIVE)
        paused = sum(1 for s in self.sessions.values() if s.status == SessionStatus.PAUSED)
        completed = sum(1 for s in self.sessions.values() if s.status == SessionStatus.COMPLETED)
        expired = sum(1 for s in self.sessions.values() if s.status == SessionStatus.EXPIRED)

        return {
            "total_sessions": len(self.sessions),
            "active": active,
            "paused": paused,
            "completed": completed,
            "expired": expired,
            "memory_bytes": sum(len(s.context.messages) for s in self.sessions.values()) * 100,
        }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(ttl_seconds: int = 3600) -> SessionManager:
    """Get or create global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(ttl_seconds=ttl_seconds)
    return _session_manager
