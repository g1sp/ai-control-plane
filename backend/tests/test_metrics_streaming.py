"""Tests for real-time metrics streaming."""

import pytest
import asyncio
from datetime import datetime
from backend.src.services.metrics_stream import (
    MetricsStreamManager,
    AnalyticsMetricsStream,
    MetricsStreamEvent,
    MetricsEventType,
    AlertLevel,
)


class TestMetricsStreamEvent:
    """Test metrics stream event model."""

    def test_create_event(self):
        """Test creating a metrics event."""
        event = MetricsStreamEvent(
            event_id="event-1",
            type=MetricsEventType.QUERY_UPDATE,
            timestamp=datetime.utcnow(),
            user_id="user1",
            data={"total_queries": 100},
        )

        assert event.event_id == "event-1"
        assert event.type == MetricsEventType.QUERY_UPDATE
        assert event.user_id == "user1"
        assert event.data["total_queries"] == 100

    def test_event_to_dict(self):
        """Test event serialization to dict."""
        now = datetime.utcnow()
        event = MetricsStreamEvent(
            event_id="event-1",
            type=MetricsEventType.COST_UPDATE,
            timestamp=now,
            data={"total_cost": 150.50},
        )

        event_dict = event.to_dict()

        assert event_dict["event_id"] == "event-1"
        assert event_dict["type"] == "cost_update"
        assert event_dict["data"]["total_cost"] == 150.50

    def test_event_from_dict(self):
        """Test event deserialization from dict."""
        data = {
            "event_id": "event-1",
            "type": "query_update",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": "user1",
            "data": {"total_queries": 50},
        }

        event = MetricsStreamEvent.from_dict(data)

        assert event.event_id == "event-1"
        assert event.type == MetricsEventType.QUERY_UPDATE
        assert event.user_id == "user1"


class TestMetricsStreamManager:
    """Test metrics stream manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MetricsStreamManager()

    def test_subscribe(self):
        """Test subscribing to metrics stream."""
        queue = self.manager.subscribe("user1")

        assert queue is not None
        assert "user1" in self.manager.subscribers

    def test_unsubscribe(self):
        """Test unsubscribing from metrics stream."""
        queue = self.manager.subscribe("user1")
        self.manager.unsubscribe("user1", queue)

        assert "user1" not in self.manager.subscribers

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test emitting an event to subscribers."""
        queue = self.manager.subscribe("user1")

        event = MetricsStreamEvent(
            event_id="event-1",
            type=MetricsEventType.QUERY_UPDATE,
            timestamp=datetime.utcnow(),
            user_id="user1",
            data={"total_queries": 100},
        )

        await self.manager.emit_event(event)

        # Event should be in history
        assert len(self.manager.event_history) == 1
        assert self.manager.event_history[0].event_id == "event-1"

        # Queue should have event
        received_event = queue.get_nowait()
        assert received_event.event_id == "event-1"

    @pytest.mark.asyncio
    async def test_emit_to_multiple_subscribers(self):
        """Test emitting to multiple subscribers."""
        queue1 = self.manager.subscribe("user1")
        queue2 = self.manager.subscribe("user1")

        event = MetricsStreamEvent(
            event_id="event-1",
            type=MetricsEventType.COST_UPDATE,
            timestamp=datetime.utcnow(),
            user_id="user1",
            data={"total_cost": 100},
        )

        await self.manager.emit_event(event)

        # Both queues should receive event
        event1 = queue1.get_nowait()
        event2 = queue2.get_nowait()

        assert event1.event_id == "event-1"
        assert event2.event_id == "event-1"

    @pytest.mark.asyncio
    async def test_emit_to_all_subscribers(self):
        """Test broadcasting to all subscribers."""
        queue_user = self.manager.subscribe("user1")
        queue_all = self.manager.subscribe("all")

        event = MetricsStreamEvent(
            event_id="event-1",
            type=MetricsEventType.QUERY_UPDATE,
            timestamp=datetime.utcnow(),
            user_id="user1",
            data={},
        )

        await self.manager.emit_event(event)

        # Both should receive event
        user_event = queue_user.get_nowait()
        all_event = queue_all.get_nowait()

        assert user_event.event_id == "event-1"
        assert all_event.event_id == "event-1"

    def test_get_subscriber_count(self):
        """Test getting subscriber count."""
        assert self.manager.get_subscriber_count() == 0

        self.manager.subscribe("user1")
        assert self.manager.get_subscriber_count() == 1

        self.manager.subscribe("user1")
        assert self.manager.get_subscriber_count() == 2

        self.manager.subscribe("user2")
        assert self.manager.get_subscriber_count() == 3

    @pytest.mark.asyncio
    async def test_history_limit(self):
        """Test that history respects max size limit."""
        # Emit more than max_history events
        for i in range(1100):
            event = MetricsStreamEvent(
                event_id=f"event-{i}",
                type=MetricsEventType.QUERY_UPDATE,
                timestamp=datetime.utcnow(),
                data={},
            )
            await self.manager.emit_event(event)

        assert len(self.manager.event_history) == 1000

    def test_get_history(self):
        """Test retrieving event history."""
        # Add some events
        events = []
        for i in range(20):
            event = MetricsStreamEvent(
                event_id=f"event-{i}",
                type=MetricsEventType.QUERY_UPDATE,
                timestamp=datetime.utcnow(),
                data={},
            )
            events.append(event)
            self.manager.event_history.append(event)

        history = self.manager.get_history(limit=10)

        assert len(history) == 10
        assert history[-1].event_id == "event-19"


class TestAnalyticsMetricsStream:
    """Test analytics metrics stream."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = MetricsStreamManager()
        self.stream = AnalyticsMetricsStream(self.manager)

    @pytest.mark.asyncio
    async def test_emit_query_update(self):
        """Test emitting query update."""
        queue = self.manager.subscribe("all")

        await self.stream.emit_query_update(
            total_queries=100,
            by_complexity={"SIMPLE": 50, "MODERATE": 30, "COMPLEX": 20},
            success_rate=0.95,
            avg_latency=150,
        )

        event = queue.get_nowait()

        assert event.type == MetricsEventType.QUERY_UPDATE
        assert event.data["total_queries"] == 100
        assert event.data["success_rate"] == 0.95

    @pytest.mark.asyncio
    async def test_emit_cost_update(self):
        """Test emitting cost update."""
        queue = self.manager.subscribe("all")

        await self.stream.emit_cost_update(
            total_cost=500.0,
            daily_cost=50.0,
            top_users=[{"user": "user1", "cost": 100.0}],
        )

        event = queue.get_nowait()

        assert event.type == MetricsEventType.COST_UPDATE
        assert event.data["total_cost"] == 500.0
        assert len(event.data["top_users"]) == 1

    @pytest.mark.asyncio
    async def test_emit_performance_update(self):
        """Test emitting performance update."""
        queue = self.manager.subscribe("all")

        await self.stream.emit_performance_update(
            avg_latency=150,
            p95_latency=300,
            p99_latency=500,
            throughput_qps=10.5,
            error_rate=0.02,
        )

        event = queue.get_nowait()

        assert event.type == MetricsEventType.PERFORMANCE_UPDATE
        assert event.data["p95_latency"] == 300
        assert event.data["throughput_qps"] == 10.5

    @pytest.mark.asyncio
    async def test_emit_session_update(self):
        """Test emitting session update."""
        queue = self.manager.subscribe("all")

        await self.stream.emit_session_update(
            active_sessions=5,
            completed_sessions=100,
            completion_rate=0.95,
        )

        event = queue.get_nowait()

        assert event.type == MetricsEventType.SESSION_UPDATE
        assert event.data["active_sessions"] == 5
        assert event.data["completion_rate"] == 0.95

    @pytest.mark.asyncio
    async def test_emit_alert(self):
        """Test emitting alert."""
        queue = self.manager.subscribe("all")

        await self.stream.emit_alert(
            level=AlertLevel.CRITICAL,
            title="High Cost Query",
            message="Query exceeded $10",
            trigger_value=15.50,
            threshold=10.0,
        )

        event = queue.get_nowait()

        assert event.type == MetricsEventType.ALERT
        assert event.data["level"] == "critical"
        assert event.data["trigger_value"] == 15.50

    @pytest.mark.asyncio
    async def test_emit_multiple_events(self):
        """Test emitting multiple event types."""
        queue = self.manager.subscribe("all")

        await self.stream.emit_query_update(100, {}, 0.95, 150)
        await self.stream.emit_cost_update(500.0, 50.0, [])
        await self.stream.emit_alert(
            AlertLevel.WARNING,
            "Test Alert",
            "Test message",
            10,
            5,
        )

        event1 = queue.get_nowait()
        event2 = queue.get_nowait()
        event3 = queue.get_nowait()

        assert event1.type == MetricsEventType.QUERY_UPDATE
        assert event2.type == MetricsEventType.COST_UPDATE
        assert event3.type == MetricsEventType.ALERT

    @pytest.mark.asyncio
    async def test_backpressure_handling(self):
        """Test that full queues are handled gracefully."""
        # Create small queue
        small_queue = asyncio.Queue(maxsize=1)
        self.manager.subscribers["user1"] = [small_queue]

        # Fill the queue
        event1 = MetricsStreamEvent(
            event_id="event-1",
            type=MetricsEventType.QUERY_UPDATE,
            timestamp=datetime.utcnow(),
            data={},
        )
        small_queue.put_nowait(event1)

        # Try to emit another - should drop silently
        event2 = MetricsStreamEvent(
            event_id="event-2",
            type=MetricsEventType.COST_UPDATE,
            timestamp=datetime.utcnow(),
            data={},
        )
        await self.manager.emit_event(event2)

        # Queue size should still be 1
        assert small_queue.qsize() == 1
