"""Real-time streaming service for agent execution."""

import asyncio
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import AsyncIterator, Callable, Optional, Dict, Any
from enum import Enum


class StreamEventType(str, Enum):
    """Event types for streaming execution."""
    START = "start"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    COST_UPDATE = "cost_update"
    ERROR = "error"
    COMPLETE = "complete"


@dataclass
class StreamEvent:
    """Single streaming event."""
    type: StreamEventType
    timestamp: datetime
    content: str
    data: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert to JSON line."""
        return json.dumps({
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "data": self.data,
        })

    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        return f"data: {self.to_json()}\n\n"


@dataclass
class StreamSession:
    """Streaming session for agent execution."""
    session_id: str
    user_id: str
    goal: str
    created_at: datetime
    events: list[StreamEvent]
    completed: bool = False
    final_response: Optional[str] = None
    total_cost_usd: float = 0.0

    def add_event(self, event: StreamEvent) -> None:
        """Add event to session."""
        self.events.append(event)

    def mark_complete(self, response: str, cost: float) -> None:
        """Mark session as complete."""
        self.completed = True
        self.final_response = response
        self.total_cost_usd = cost
        self.add_event(StreamEvent(
            type=StreamEventType.COMPLETE,
            timestamp=datetime.utcnow(),
            content=response,
            data={"cost_usd": cost}
        ))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "goal": self.goal,
            "created_at": self.created_at.isoformat(),
            "completed": self.completed,
            "final_response": self.final_response,
            "total_cost_usd": self.total_cost_usd,
            "events": [asdict(e) for e in self.events],
        }


class StreamManager:
    """Manages streaming sessions and event distribution."""

    def __init__(self):
        """Initialize stream manager."""
        self.sessions: Dict[str, StreamSession] = {}
        self.subscribers: Dict[str, list[asyncio.Queue]] = {}

    def create_session(self, user_id: str, goal: str) -> str:
        """Create new streaming session."""
        session_id = str(uuid.uuid4())
        session = StreamSession(
            session_id=session_id,
            user_id=user_id,
            goal=goal,
            created_at=datetime.utcnow(),
            events=[]
        )
        self.sessions[session_id] = session
        self.subscribers[session_id] = []
        return session_id

    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        """Subscribe to session events."""
        if session_id not in self.subscribers:
            self.subscribers[session_id] = []

        queue = asyncio.Queue()
        self.subscribers[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from session events."""
        if session_id in self.subscribers:
            try:
                self.subscribers[session_id].remove(queue)
            except ValueError:
                pass

    async def emit_event(self, session_id: str, event: StreamEvent) -> None:
        """Emit event to all subscribers."""
        session = self.get_session(session_id)
        if session:
            session.add_event(event)

            if session_id in self.subscribers:
                for queue in self.subscribers[session_id]:
                    try:
                        queue.put_nowait(event)
                    except asyncio.QueueFull:
                        pass

    async def stream_events(self, session_id: str) -> AsyncIterator[StreamEvent]:
        """Stream events from session."""
        session = self.get_session(session_id)
        if not session:
            return

        # Send existing events first
        for event in session.events:
            yield event

        # Subscribe to new events
        queue = self.subscribe(session_id)
        try:
            while not session.completed:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=60.0)
                    yield event
                except asyncio.TimeoutError:
                    break
        finally:
            self.unsubscribe(session_id, queue)

    def cleanup_session(self, session_id: str) -> None:
        """Cleanup session after completion."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.subscribers:
            del self.subscribers[session_id]


class StreamingEventCallback:
    """Callback interface for agent execution streaming."""

    def __init__(self, manager: StreamManager, session_id: str):
        """Initialize callback."""
        self.manager = manager
        self.session_id = session_id

    async def on_thinking(self, content: str) -> None:
        """Agent is thinking."""
        event = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime.utcnow(),
            content=content
        )
        await self.manager.emit_event(self.session_id, event)

    async def on_tool_call(self, tool_name: str, args: Dict[str, Any]) -> None:
        """Tool is being called."""
        event = StreamEvent(
            type=StreamEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            content=f"Calling {tool_name}",
            data={"tool": tool_name, "args": args}
        )
        await self.manager.emit_event(self.session_id, event)

    async def on_tool_result(self, tool_name: str, result: str) -> None:
        """Tool returned result."""
        event = StreamEvent(
            type=StreamEventType.TOOL_RESULT,
            timestamp=datetime.utcnow(),
            content=f"Result from {tool_name}: {result[:100]}...",
            data={"tool": tool_name, "result": result}
        )
        await self.manager.emit_event(self.session_id, event)

    async def on_cost_update(self, tokens_in: int, tokens_out: int, cost_usd: float) -> None:
        """Cost has been updated."""
        event = StreamEvent(
            type=StreamEventType.COST_UPDATE,
            timestamp=datetime.utcnow(),
            content=f"Cost: ${cost_usd:.4f} ({tokens_in}→{tokens_out} tokens)",
            data={"tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": cost_usd}
        )
        await self.manager.emit_event(self.session_id, event)

    async def on_error(self, error: str) -> None:
        """Error occurred."""
        event = StreamEvent(
            type=StreamEventType.ERROR,
            timestamp=datetime.utcnow(),
            content=error,
            data={"error": error}
        )
        await self.manager.emit_event(self.session_id, event)


# Global stream manager instance
_stream_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """Get or create global stream manager."""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager
