"""Alert trigger system for real-time anomaly detection and notifications."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio

from .metrics_stream import (
    AlertLevel,
    MetricsStreamEvent,
    MetricsEventType,
    AnalyticsMetricsStream,
)


class AlertTriggerType(str, Enum):
    """Types of alert triggers."""
    HIGH_COST_QUERY = "high_cost_query"
    SLOW_QUERY = "slow_query"
    ERROR_SPIKE = "error_spike"
    COST_BUDGET_EXCEEDED = "cost_budget_exceeded"
    SYSTEM_DEGRADATION = "system_degradation"
    QUERY_FAILURE = "query_failure"


@dataclass
class AlertTriggerConfig:
    """Configuration for an alert trigger."""
    trigger_type: AlertTriggerType
    enabled: bool
    threshold: float
    duration_seconds: int = 0  # For time-window based triggers
    alert_level: AlertLevel = AlertLevel.WARNING
    debounce_seconds: int = 60  # Minimum time between alerts
    description: str = ""


@dataclass
class AlertMetrics:
    """Metrics state for trigger evaluation."""
    total_queries: int = 0
    failed_queries: int = 0
    total_cost: float = 0.0
    avg_latency: float = 0.0
    max_latency: float = 0.0
    error_rate: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AlertTriggerEngine:
    """Engine for evaluating alert triggers and generating alerts."""

    def __init__(self, analytics_stream: Optional[AnalyticsMetricsStream] = None):
        """Initialize alert trigger engine."""
        self.analytics_stream = analytics_stream
        self.triggers: Dict[str, AlertTriggerConfig] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        self.metrics_history: List[AlertMetrics] = []
        self.max_history = 1000

        # Initialize default triggers
        self._init_default_triggers()

    def _init_default_triggers(self) -> None:
        """Initialize default alert triggers."""
        self.triggers = {
            AlertTriggerType.HIGH_COST_QUERY: AlertTriggerConfig(
                trigger_type=AlertTriggerType.HIGH_COST_QUERY,
                enabled=True,
                threshold=10.0,  # $10 per query
                alert_level=AlertLevel.WARNING,
                description="Query cost exceeds $10",
            ),
            AlertTriggerType.SLOW_QUERY: AlertTriggerConfig(
                trigger_type=AlertTriggerType.SLOW_QUERY,
                enabled=True,
                threshold=2000.0,  # 2000ms
                alert_level=AlertLevel.WARNING,
                description="Query latency exceeds 2 seconds",
            ),
            AlertTriggerType.ERROR_SPIKE: AlertTriggerConfig(
                trigger_type=AlertTriggerType.ERROR_SPIKE,
                enabled=True,
                threshold=0.05,  # 5% error rate
                duration_seconds=300,  # Over 5 minutes
                alert_level=AlertLevel.CRITICAL,
                description="Error rate exceeds 5%",
            ),
            AlertTriggerType.COST_BUDGET_EXCEEDED: AlertTriggerConfig(
                trigger_type=AlertTriggerType.COST_BUDGET_EXCEEDED,
                enabled=True,
                threshold=1000.0,  # $1000 daily budget
                alert_level=AlertLevel.CRITICAL,
                description="Daily cost budget exceeded",
            ),
            AlertTriggerType.SYSTEM_DEGRADATION: AlertTriggerConfig(
                trigger_type=AlertTriggerType.SYSTEM_DEGRADATION,
                enabled=True,
                threshold=0.5,  # 50% latency increase
                duration_seconds=600,  # Over 10 minutes
                alert_level=AlertLevel.WARNING,
                description="System latency degraded 50%",
            ),
        }

    def update_config(
        self,
        trigger_type: AlertTriggerType,
        config: AlertTriggerConfig,
    ) -> None:
        """Update trigger configuration."""
        self.triggers[trigger_type.value] = config

    def get_config(self, trigger_type: AlertTriggerType) -> Optional[AlertTriggerConfig]:
        """Get trigger configuration."""
        return self.triggers.get(trigger_type.value)

    def record_metrics(self, metrics: AlertMetrics) -> None:
        """Record metrics snapshot for trend analysis."""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)

    async def evaluate_triggers(self, metrics: AlertMetrics) -> List[MetricsStreamEvent]:
        """Evaluate all triggers and return generated alerts."""
        self.record_metrics(metrics)
        alerts: List[MetricsStreamEvent] = []

        for trigger_type, config in self.triggers.items():
            if not config.enabled:
                continue

            should_alert = False
            alert_title = ""
            alert_message = ""

            # Evaluate trigger
            if trigger_type == AlertTriggerType.HIGH_COST_QUERY.value:
                should_alert = metrics.total_cost > config.threshold
                alert_title = "High Cost Query Detected"
                alert_message = f"Query cost (${metrics.total_cost:.2f}) exceeds threshold (${config.threshold:.2f})"

            elif trigger_type == AlertTriggerType.SLOW_QUERY.value:
                should_alert = metrics.max_latency > config.threshold
                alert_title = "Slow Query Detected"
                alert_message = f"Query latency ({metrics.max_latency:.0f}ms) exceeds threshold ({config.threshold:.0f}ms)"

            elif trigger_type == AlertTriggerType.ERROR_SPIKE.value:
                should_alert = metrics.error_rate > config.threshold
                alert_title = "Error Rate Spike"
                alert_message = f"Error rate ({metrics.error_rate:.1%}) exceeds threshold ({config.threshold:.1%}) over {config.duration_seconds}s"

            elif trigger_type == AlertTriggerType.COST_BUDGET_EXCEEDED.value:
                should_alert = metrics.total_cost > config.threshold
                alert_title = "Daily Budget Exceeded"
                alert_message = f"Daily cost (${metrics.total_cost:.2f}) exceeds budget (${config.threshold:.2f})"

            elif trigger_type == AlertTriggerType.SYSTEM_DEGRADATION.value:
                latency_increase = self._calculate_latency_increase(metrics)
                should_alert = latency_increase > config.threshold
                alert_title = "System Degradation Detected"
                alert_message = f"Latency increased {latency_increase:.0%} over {config.duration_seconds}s"

            # Check debounce
            if should_alert:
                trigger_key = trigger_type
                now = datetime.utcnow()
                last_time = self.last_alert_time.get(trigger_key)

                if last_time is None or (now - last_time).total_seconds() > config.debounce_seconds:
                    alert = MetricsStreamEvent(
                        event_id=f"alert-{trigger_type}-{int(now.timestamp())}",
                        type=MetricsEventType.ALERT,
                        timestamp=now,
                        data={
                            "level": config.alert_level.value,
                            "title": alert_title,
                            "message": alert_message,
                            "trigger_type": trigger_type,
                            "trigger_value": metrics.total_cost if trigger_type in [
                                AlertTriggerType.HIGH_COST_QUERY.value,
                                AlertTriggerType.COST_BUDGET_EXCEEDED.value,
                            ] else metrics.max_latency if trigger_type == AlertTriggerType.SLOW_QUERY.value else metrics.error_rate,
                            "threshold": config.threshold,
                        },
                    )
                    alerts.append(alert)
                    self.last_alert_time[trigger_key] = now

                    # Emit alert via analytics stream
                    if self.analytics_stream:
                        await self.analytics_stream.emit_alert(
                            level=config.alert_level,
                            title=alert_title,
                            message=alert_message,
                            trigger_value=alert.data.get("trigger_value"),
                            threshold=config.threshold,
                        )

        return alerts

    def _calculate_latency_increase(self, current_metrics: AlertMetrics) -> float:
        """Calculate latency increase over time window."""
        if len(self.metrics_history) < 2:
            return 0.0

        # Find metrics from specified duration ago
        duration_seconds = self.triggers[
            AlertTriggerType.SYSTEM_DEGRADATION.value
        ].duration_seconds
        cutoff_time = datetime.utcnow() - timedelta(seconds=duration_seconds)

        previous_metrics = None
        for metrics in reversed(self.metrics_history):
            if metrics.timestamp <= cutoff_time:
                previous_metrics = metrics
                break

        if previous_metrics is None or previous_metrics.avg_latency == 0:
            return 0.0

        increase = (current_metrics.avg_latency - previous_metrics.avg_latency) / previous_metrics.avg_latency
        return max(0.0, increase)

    def get_active_alerts(self) -> Dict[str, datetime]:
        """Get currently active alerts (triggers that have fired recently)."""
        return dict(self.last_alert_time)

    def get_metrics_history(self, limit: int = 100) -> List[AlertMetrics]:
        """Get recent metrics history."""
        return self.metrics_history[-limit:]

    def reset_trigger(self, trigger_type: AlertTriggerType) -> None:
        """Reset trigger debounce timer (clear last alert)."""
        trigger_key = trigger_type.value
        if trigger_key in self.last_alert_time:
            del self.last_alert_time[trigger_key]

    def clear_all_triggers(self) -> None:
        """Clear all trigger states."""
        self.last_alert_time.clear()


# Global instance
_alert_engine: Optional[AlertTriggerEngine] = None


def get_alert_engine(analytics_stream: Optional[AnalyticsMetricsStream] = None) -> AlertTriggerEngine:
    """Get or create global alert trigger engine."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertTriggerEngine(analytics_stream)
    return _alert_engine
