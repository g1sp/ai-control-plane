"""Real-time metrics streaming service for dashboard updates."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import uuid


class MetricsEventType(str, Enum):
    """Types of metrics events."""
    QUERY_UPDATE = "query_update"
    USER_UPDATE = "user_update"
    COST_UPDATE = "cost_update"
    PERFORMANCE_UPDATE = "performance_update"
    SESSION_UPDATE = "session_update"
    ALERT = "alert"


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricsStreamEvent:
    """Real-time metrics event."""
    event_id: str
    type: MetricsEventType
    timestamp: datetime
    user_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "data": self.data or {},
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MetricsStreamEvent":
        """Create from dictionary."""
        return MetricsStreamEvent(
            event_id=data.get("event_id", str(uuid.uuid4())),
            type=MetricsEventType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            data=data.get("data"),
        )


@dataclass
class AlertEvent:
    """Alert event with trigger information."""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    trigger_value: Any
    threshold: Any
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "trigger_value": trigger_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsStreamManager:
    """Manage real-time metrics streaming to connected clients."""

    def __init__(self):
        """Initialize metrics stream manager."""
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.event_history: List[MetricsStreamEvent] = []
        self.max_history = 1000  # Keep last 1000 events

    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Subscribe to metrics stream for user."""
        queue = asyncio.Queue(maxsize=100)

        if user_id not in self.subscribers:
            self.subscribers[user_id] = []

        self.subscribers[user_id].append(queue)
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from metrics stream."""
        if user_id in self.subscribers:
            try:
                self.subscribers[user_id].remove(queue)
            except ValueError:
                pass

            if not self.subscribers[user_id]:
                del self.subscribers[user_id]

    async def emit_event(self, event: MetricsStreamEvent) -> None:
        """Emit metrics event to all subscribers."""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Broadcast to subscribers
        user_id = event.user_id or "all"
        if user_id in self.subscribers:
            for queue in self.subscribers[user_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass  # Drop event if queue full (backpressure)

        # Also send to "all" subscribers if not already sent
        if user_id != "all" and "all" in self.subscribers:
            for queue in self.subscribers["all"]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass

    async def stream_events(self, user_id: str) -> None:
        """Stream events for user (async generator pattern)."""
        queue = self.subscribe(user_id)

        try:
            # Send recent history first
            for event in self.event_history[-10:]:
                try:
                    yield event
                except GeneratorExit:
                    return

            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=60)
                    yield event
                except asyncio.TimeoutError:
                    break
        finally:
            self.unsubscribe(user_id, queue)

    def get_subscriber_count(self) -> int:
        """Get total number of active subscribers."""
        return sum(len(queues) for queues in self.subscribers.values())

    def get_history(self, limit: int = 50) -> List[MetricsStreamEvent]:
        """Get recent event history."""
        return self.event_history[-limit:]


class AnalyticsMetricsStream:
    """Collect and stream real-time analytics metrics."""

    def __init__(self, manager: Optional[MetricsStreamManager] = None):
        """Initialize analytics metrics stream."""
        self.manager = manager or MetricsStreamManager()
        self.last_query_count = 0
        self.last_cost = 0.0
        self.last_latency = 0

    async def emit_query_update(
        self,
        total_queries: int,
        by_complexity: Dict[str, int],
        success_rate: float,
        avg_latency: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Emit query metrics update."""
        event = MetricsStreamEvent(
            event_id=str(uuid.uuid4()),
            type=MetricsEventType.QUERY_UPDATE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            data={
                "total_queries": total_queries,
                "by_complexity": by_complexity,
                "success_rate": success_rate,
                "avg_latency": avg_latency,
            },
        )
        await self.manager.emit_event(event)

    async def emit_cost_update(
        self,
        total_cost: float,
        daily_cost: float,
        top_users: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> None:
        """Emit cost metrics update."""
        event = MetricsStreamEvent(
            event_id=str(uuid.uuid4()),
            type=MetricsEventType.COST_UPDATE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            data={
                "total_cost": total_cost,
                "daily_cost": daily_cost,
                "top_users": top_users,
            },
        )
        await self.manager.emit_event(event)

    async def emit_performance_update(
        self,
        avg_latency: float,
        p95_latency: float,
        p99_latency: float,
        throughput_qps: float,
        error_rate: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Emit performance metrics update."""
        event = MetricsStreamEvent(
            event_id=str(uuid.uuid4()),
            type=MetricsEventType.PERFORMANCE_UPDATE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            data={
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "p99_latency": p99_latency,
                "throughput_qps": throughput_qps,
                "error_rate": error_rate,
            },
        )
        await self.manager.emit_event(event)

    async def emit_session_update(
        self,
        active_sessions: int,
        completed_sessions: int,
        completion_rate: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Emit session metrics update."""
        event = MetricsStreamEvent(
            event_id=str(uuid.uuid4()),
            type=MetricsEventType.SESSION_UPDATE,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            data={
                "active_sessions": active_sessions,
                "completed_sessions": completed_sessions,
                "completion_rate": completion_rate,
            },
        )
        await self.manager.emit_event(event)

    async def emit_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        trigger_value: Any,
        threshold: Any,
        user_id: Optional[str] = None,
    ) -> None:
        """Emit alert event."""
        event = MetricsStreamEvent(
            event_id=str(uuid.uuid4()),
            type=MetricsEventType.ALERT,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            data={
                "level": level.value,
                "title": title,
                "message": message,
                "trigger_value": trigger_value,
                "threshold": threshold,
            },
        )
        await self.manager.emit_event(event)


# Global instances
_metrics_manager: Optional[MetricsStreamManager] = None
_analytics_metrics: Optional[AnalyticsMetricsStream] = None


def get_metrics_manager() -> MetricsStreamManager:
    """Get or create global metrics stream manager."""
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = MetricsStreamManager()
    return _metrics_manager


def get_analytics_metrics() -> AnalyticsMetricsStream:
    """Get or create global analytics metrics stream."""
    global _analytics_metrics
    if _analytics_metrics is None:
        manager = get_metrics_manager()
        _analytics_metrics = AnalyticsMetricsStream(manager)
    return _analytics_metrics
