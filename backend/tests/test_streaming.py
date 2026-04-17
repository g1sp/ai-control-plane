"""Tests for real-time streaming service."""

import pytest
import asyncio
from datetime import datetime
from src.services.streaming import (
    StreamManager, StreamSession, StreamEvent, StreamEventType,
    StreamingEventCallback, get_stream_manager
)


class TestStreamManager:
    """Test stream manager functionality."""

    def test_create_session(self):
        """Test session creation."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test goal")

        assert session_id is not None
        session = manager.get_session(session_id)
        assert session is not None
        assert session.user_id == "user@example.com"
        assert session.goal == "Test goal"
        assert session.completed is False

    def test_get_nonexistent_session(self):
        """Test getting non-existent session."""
        manager = StreamManager()
        session = manager.get_session("nonexistent")
        assert session is None

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test event emission."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        event = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime.utcnow(),
            content="Thinking about this..."
        )

        await manager.emit_event(session_id, event)
        session = manager.get_session(session_id)
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.THINKING

    @pytest.mark.asyncio
    async def test_subscribe_and_stream(self):
        """Test subscribing and streaming events."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        # Start streaming in background
        events_received = []

        async def collect_events():
            count = 0
            async for event in manager.stream_events(session_id):
                events_received.append(event)
                count += 1
                if count >= 3:  # Wait for 3 events including COMPLETE
                    break

        # Emit events
        event1 = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime.utcnow(),
            content="First thought"
        )
        event2 = StreamEvent(
            type=StreamEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            content="Calling search"
        )

        task = asyncio.create_task(collect_events())

        await asyncio.sleep(0.05)
        await manager.emit_event(session_id, event1)
        await asyncio.sleep(0.05)
        await manager.emit_event(session_id, event2)
        await asyncio.sleep(0.05)

        session = manager.get_session(session_id)
        session.mark_complete("Done", 0.01)

        try:
            await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

        assert len(events_received) >= 2

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Test multiple subscribers to same session."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        queues = [manager.subscribe(session_id) for _ in range(3)]

        event = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime.utcnow(),
            content="Test event"
        )

        await manager.emit_event(session_id, event)

        # All subscribers should receive event
        for queue in queues:
            received_event = queue.get_nowait()
            assert received_event.type == StreamEventType.THINKING

    def test_cleanup_session(self):
        """Test session cleanup."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        assert manager.get_session(session_id) is not None
        manager.cleanup_session(session_id)
        assert manager.get_session(session_id) is None


class TestStreamSession:
    """Test stream session functionality."""

    def test_add_event(self):
        """Test adding event to session."""
        session = StreamSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test",
            created_at=datetime.utcnow(),
            events=[]
        )

        event = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime.utcnow(),
            content="Test"
        )

        session.add_event(event)
        assert len(session.events) == 1

    def test_mark_complete(self):
        """Test marking session complete."""
        session = StreamSession(
            session_id="test",
            user_id="user@example.com",
            goal="Test",
            created_at=datetime.utcnow(),
            events=[]
        )

        assert session.completed is False

        session.mark_complete("Final response", 0.015)

        assert session.completed is True
        assert session.final_response == "Final response"
        assert session.total_cost_usd == 0.015
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.COMPLETE

    def test_to_dict(self):
        """Test session serialization."""
        session = StreamSession(
            session_id="test123",
            user_id="user@example.com",
            goal="Test goal",
            created_at=datetime.utcnow(),
            events=[]
        )

        data = session.to_dict()
        assert data["session_id"] == "test123"
        assert data["user_id"] == "user@example.com"
        assert data["goal"] == "Test goal"
        assert data["completed"] is False


class TestStreamEvent:
    """Test stream event serialization."""

    def test_event_to_json(self):
        """Test event JSON serialization."""
        event = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime(2026, 4, 16, 12, 0, 0),
            content="Thinking...",
            data={"test": "data"}
        )

        json_str = event.to_json()
        assert "thinking" in json_str
        assert "Thinking..." in json_str
        assert "test" in json_str

    def test_event_to_sse(self):
        """Test event SSE format."""
        event = StreamEvent(
            type=StreamEventType.TOOL_CALL,
            timestamp=datetime.utcnow(),
            content="Calling search"
        )

        sse_str = event.to_sse()
        assert sse_str.startswith("data: ")
        assert sse_str.endswith("\n\n")
        assert "tool_call" in sse_str


class TestStreamingEventCallback:
    """Test streaming event callbacks."""

    @pytest.mark.asyncio
    async def test_on_thinking(self):
        """Test thinking callback."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")
        callback = StreamingEventCallback(manager, session_id)

        await callback.on_thinking("Analyzing the problem...")

        session = manager.get_session(session_id)
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.THINKING
        assert "Analyzing" in session.events[0].content

    @pytest.mark.asyncio
    async def test_on_tool_call(self):
        """Test tool call callback."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")
        callback = StreamingEventCallback(manager, session_id)

        await callback.on_tool_call("search", {"query": "test"})

        session = manager.get_session(session_id)
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.TOOL_CALL
        assert session.events[0].data["tool"] == "search"

    @pytest.mark.asyncio
    async def test_on_tool_result(self):
        """Test tool result callback."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")
        callback = StreamingEventCallback(manager, session_id)

        await callback.on_tool_result("search", "Found: result 1, result 2")

        session = manager.get_session(session_id)
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.TOOL_RESULT

    @pytest.mark.asyncio
    async def test_on_cost_update(self):
        """Test cost update callback."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")
        callback = StreamingEventCallback(manager, session_id)

        await callback.on_cost_update(100, 50, 0.015)

        session = manager.get_session(session_id)
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.COST_UPDATE
        assert session.events[0].data["cost_usd"] == 0.015

    @pytest.mark.asyncio
    async def test_on_error(self):
        """Test error callback."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")
        callback = StreamingEventCallback(manager, session_id)

        await callback.on_error("Tool execution failed")

        session = manager.get_session(session_id)
        assert len(session.events) == 1
        assert session.events[0].type == StreamEventType.ERROR
        assert "failed" in session.events[0].content


class TestGlobalStreamManager:
    """Test global stream manager singleton."""

    def test_get_stream_manager(self):
        """Test getting global stream manager."""
        manager1 = get_stream_manager()
        manager2 = get_stream_manager()
        assert manager1 is manager2


class TestStreamingIntegration:
    """Integration tests for streaming."""

    @pytest.mark.asyncio
    async def test_full_execution_stream(self):
        """Test full agent execution streaming."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "What is 2+2?")
        callback = StreamingEventCallback(manager, session_id)

        # Simulate agent execution
        await callback.on_thinking("This is a math problem")
        await callback.on_tool_call("python_eval", {"code": "2 + 2"})
        await callback.on_cost_update(50, 10, 0.0005)
        await callback.on_tool_result("python_eval", "4")

        session = manager.get_session(session_id)
        assert len(session.events) == 4

        session.mark_complete("The answer is 4", 0.001)
        assert session.completed is True
        assert len(session.events) == 5

    @pytest.mark.asyncio
    async def test_stream_with_timeout(self):
        """Test streaming with timeout."""
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        events_received = []

        async def collect_with_timeout():
            async for event in manager.stream_events(session_id):
                events_received.append(event)

        task = asyncio.create_task(collect_with_timeout())

        await asyncio.sleep(0.1)
        event = StreamEvent(
            type=StreamEventType.THINKING,
            timestamp=datetime.utcnow(),
            content="Test"
        )
        await manager.emit_event(session_id, event)

        session = manager.get_session(session_id)
        session.mark_complete("Done", 0.0)

        try:
            await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

        assert len(events_received) >= 1


class TestStreamPerformance:
    """Performance tests for streaming."""

    @pytest.mark.asyncio
    async def test_event_emission_latency(self):
        """Test event emission latency."""
        import time
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        start = time.time()
        for _ in range(100):
            event = StreamEvent(
                type=StreamEventType.THINKING,
                timestamp=datetime.utcnow(),
                content="Test"
            )
            await manager.emit_event(session_id, event)
        elapsed = (time.time() - start) * 1000

        # Should emit 100 events in <50ms (0.5ms per event)
        assert elapsed < 50

    @pytest.mark.asyncio
    async def test_streaming_throughput(self):
        """Test streaming throughput."""
        import time
        manager = StreamManager()
        session_id = manager.create_session("user@example.com", "Test")

        received = 0

        async def emit_rapidly():
            for i in range(50):
                event = StreamEvent(
                    type=StreamEventType.THINKING,
                    timestamp=datetime.utcnow(),
                    content=f"Event {i}"
                )
                await manager.emit_event(session_id, event)
                await asyncio.sleep(0.01)

        async def collect():
            nonlocal received
            start = time.time()
            async for event in manager.stream_events(session_id):
                received += 1
                if received >= 50:
                    break
            elapsed = (time.time() - start) * 1000
            return elapsed

        emit_task = asyncio.create_task(emit_rapidly())
        collect_task = asyncio.create_task(collect())

        await emit_task

        session = manager.get_session(session_id)
        session.mark_complete("Done", 0.0)

        elapsed = await collect_task

        assert received == 50
        # 50 events in less than 2 seconds
        assert elapsed < 2000
