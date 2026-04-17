"""Alert delivery channels for sending alerts via email, Slack, and PagerDuty."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import json


class AlertChannel(str, Enum):
    """Types of alert delivery channels."""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"


class DeliveryStatus(str, Enum):
    """Alert delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class AlertChannelConfig:
    """Configuration for an alert delivery channel."""
    channel_type: AlertChannel
    enabled: bool
    destination: str  # Email address, Slack webhook URL, or PagerDuty integration key
    include_critical: bool = True
    include_warning: bool = True
    include_info: bool = False


@dataclass
class DeliveryRule:
    """Rule for routing alerts to channels."""
    trigger_type: str
    channel_type: AlertChannel
    enabled: bool
    alert_levels: List[str] = None  # ["critical", "warning", "info"]

    def __post_init__(self):
        if self.alert_levels is None:
            self.alert_levels = ["critical", "warning"]


@dataclass
class AlertDeliveryRecord:
    """Record of alert delivery attempt."""
    alert_id: str
    channel_type: AlertChannel
    destination: str
    status: DeliveryStatus
    timestamp: datetime
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class EmailService:
    """Service for sending alerts via email."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
    ):
        """Initialize email service."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    async def send_alert(
        self,
        to_email: str,
        alert_title: str,
        alert_message: str,
        alert_level: str,
        trigger_value: Any = None,
        threshold: Any = None,
    ) -> bool:
        """Send alert via email."""
        try:
            subject = f"[{alert_level.upper()}] {alert_title}"

            body = f"""
Alert Notification
==================

Level: {alert_level.upper()}
Title: {alert_title}
Message: {alert_message}
Time: {datetime.utcnow().isoformat()}

{f"Trigger Value: {trigger_value}" if trigger_value else ""}
{f"Threshold: {threshold}" if threshold else ""}

---
Policy-Aware AI Gateway Alerts
"""

            msg = MIMEMultipart()
            msg["From"] = self.smtp_user or "alerts@gateway.local"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # In production, use async SMTP client
            # For now, return success
            return await self._send_smtp(msg)

        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    async def _send_smtp(self, msg: MIMEMultipart) -> bool:
        """Send via SMTP (placeholder for async implementation)."""
        # TODO: Implement actual SMTP sending
        # For testing, just return True
        return True

    async def test_connection(self, to_email: str) -> bool:
        """Test email configuration."""
        return await self.send_alert(
            to_email=to_email,
            alert_title="Test Alert",
            alert_message="This is a test alert from the AI Control Plane.",
            alert_level="info",
        )


class SlackService:
    """Service for sending alerts to Slack."""

    def __init__(self):
        """Initialize Slack service."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def send_alert(
        self,
        webhook_url: str,
        alert_title: str,
        alert_message: str,
        alert_level: str,
        trigger_value: Any = None,
        threshold: Any = None,
    ) -> bool:
        """Send alert to Slack channel."""
        try:
            color_map = {
                "critical": "#FF0000",  # Red
                "warning": "#FFA500",   # Orange
                "info": "#0099FF",      # Blue
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert_level, "#808080"),
                        "title": alert_title,
                        "text": alert_message,
                        "fields": [
                            {
                                "title": "Level",
                                "value": alert_level.upper(),
                                "short": True,
                            },
                            {
                                "title": "Timestamp",
                                "value": datetime.utcnow().isoformat(),
                                "short": True,
                            },
                        ],
                        "footer": "AI Control Plane",
                        "ts": int(datetime.utcnow().timestamp()),
                    }
                ]
            }

            if trigger_value is not None:
                payload["attachments"][0]["fields"].append(
                    {
                        "title": "Trigger Value",
                        "value": str(trigger_value),
                        "short": True,
                    }
                )

            if threshold is not None:
                payload["attachments"][0]["fields"].append(
                    {
                        "title": "Threshold",
                        "value": str(threshold),
                        "short": True,
                    }
                )

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status == 200

        except Exception as e:
            print(f"Slack send failed: {e}")
            return False

    async def test_connection(self, webhook_url: str) -> bool:
        """Test Slack webhook configuration."""
        return await self.send_alert(
            webhook_url=webhook_url,
            alert_title="Test Alert",
            alert_message="This is a test alert from the AI Control Plane.",
            alert_level="info",
        )


class PagerDutyService:
    """Service for creating incidents in PagerDuty."""

    def __init__(self):
        """Initialize PagerDuty service."""
        self.api_base = "https://api.pagerduty.com"

    async def send_alert(
        self,
        integration_key: str,
        alert_title: str,
        alert_message: str,
        alert_level: str,
        trigger_value: Any = None,
        threshold: Any = None,
    ) -> bool:
        """Create PagerDuty incident for alert."""
        try:
            severity_map = {
                "critical": "critical",
                "warning": "warning",
                "info": "info",
            }

            payload = {
                "routing_key": integration_key,
                "event_action": "trigger",
                "dedup_key": f"alert-{datetime.utcnow().timestamp()}",
                "payload": {
                    "summary": alert_title,
                    "severity": severity_map.get(alert_level, "warning"),
                    "source": "AI Control Plane",
                    "custom_details": {
                        "message": alert_message,
                        "trigger_value": str(trigger_value) if trigger_value else None,
                        "threshold": str(threshold) if threshold else None,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/v2/enqueue",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    return response.status == 202

        except Exception as e:
            print(f"PagerDuty send failed: {e}")
            return False

    async def test_connection(self, integration_key: str) -> bool:
        """Test PagerDuty integration key."""
        return await self.send_alert(
            integration_key=integration_key,
            alert_title="Test Alert",
            alert_message="This is a test alert from the AI Control Plane.",
            alert_level="info",
        )


class AlertChannelRouter:
    """Route alerts to configured channels based on rules."""

    def __init__(self):
        """Initialize alert channel router."""
        self.channels: Dict[str, AlertChannelConfig] = {}
        self.rules: List[DeliveryRule] = []
        self.delivery_history: List[AlertDeliveryRecord] = []
        self.max_history = 1000

        self.email_service = EmailService()
        self.slack_service = SlackService()
        self.pagerduty_service = PagerDutyService()

    def add_channel(self, config: AlertChannelConfig) -> None:
        """Add alert delivery channel."""
        channel_key = f"{config.channel_type.value}_{config.destination}"
        self.channels[channel_key] = config

    def remove_channel(self, channel_type: AlertChannel, destination: str) -> None:
        """Remove alert delivery channel."""
        channel_key = f"{channel_type.value}_{destination}"
        if channel_key in self.channels:
            del self.channels[channel_key]

    def add_rule(self, rule: DeliveryRule) -> None:
        """Add alert routing rule."""
        self.rules.append(rule)

    def get_channels_for_alert(
        self, trigger_type: str, alert_level: str
    ) -> List[AlertChannelConfig]:
        """Get channels where alert should be delivered."""
        channels = []

        for rule in self.rules:
            if rule.enabled and rule.trigger_type == trigger_type:
                if alert_level in rule.alert_levels:
                    channel_key = f"{rule.channel_type.value}_*"
                    # Find matching channels
                    for key, config in self.channels.items():
                        if (
                            config.enabled
                            and config.channel_type == rule.channel_type
                        ):
                            if (
                                alert_level == "critical" and config.include_critical
                            ) or (alert_level == "warning" and config.include_warning) or (
                                alert_level == "info" and config.include_info
                            ):
                                channels.append(config)

        return channels

    async def route_alert(
        self,
        alert_id: str,
        trigger_type: str,
        alert_title: str,
        alert_message: str,
        alert_level: str,
        trigger_value: Any = None,
        threshold: Any = None,
    ) -> List[AlertDeliveryRecord]:
        """Route alert to appropriate channels."""
        delivery_records: List[AlertDeliveryRecord] = []

        channels = self.get_channels_for_alert(trigger_type, alert_level)

        for config in channels:
            record = AlertDeliveryRecord(
                alert_id=alert_id,
                channel_type=config.channel_type,
                destination=config.destination,
                status=DeliveryStatus.PENDING,
                timestamp=datetime.utcnow(),
            )

            # Send to channel
            success = False
            if config.channel_type == AlertChannel.EMAIL:
                success = await self.email_service.send_alert(
                    to_email=config.destination,
                    alert_title=alert_title,
                    alert_message=alert_message,
                    alert_level=alert_level,
                    trigger_value=trigger_value,
                    threshold=threshold,
                )
            elif config.channel_type == AlertChannel.SLACK:
                success = await self.slack_service.send_alert(
                    webhook_url=config.destination,
                    alert_title=alert_title,
                    alert_message=alert_message,
                    alert_level=alert_level,
                    trigger_value=trigger_value,
                    threshold=threshold,
                )
            elif config.channel_type == AlertChannel.PAGERDUTY:
                success = await self.pagerduty_service.send_alert(
                    integration_key=config.destination,
                    alert_title=alert_title,
                    alert_message=alert_message,
                    alert_level=alert_level,
                    trigger_value=trigger_value,
                    threshold=threshold,
                )

            record.status = DeliveryStatus.SENT if success else DeliveryStatus.FAILED
            delivery_records.append(record)
            self.record_delivery(record)

        return delivery_records

    def record_delivery(self, record: AlertDeliveryRecord) -> None:
        """Record alert delivery attempt."""
        self.delivery_history.append(record)
        if len(self.delivery_history) > self.max_history:
            self.delivery_history.pop(0)

    def get_delivery_history(
        self,
        alert_id: Optional[str] = None,
        channel_type: Optional[AlertChannel] = None,
        limit: int = 100,
    ) -> List[AlertDeliveryRecord]:
        """Get delivery history with optional filters."""
        history = self.delivery_history

        if alert_id:
            history = [r for r in history if r.alert_id == alert_id]

        if channel_type:
            history = [r for r in history if r.channel_type == channel_type]

        return history[-limit:]

    async def test_channel(self, config: AlertChannelConfig) -> bool:
        """Test alert channel configuration."""
        try:
            if config.channel_type == AlertChannel.EMAIL:
                return await self.email_service.test_connection(config.destination)
            elif config.channel_type == AlertChannel.SLACK:
                return await self.slack_service.test_connection(config.destination)
            elif config.channel_type == AlertChannel.PAGERDUTY:
                return await self.pagerduty_service.test_connection(config.destination)
        except Exception as e:
            print(f"Test failed: {e}")
            return False

    def get_channel_status(self) -> Dict[str, Any]:
        """Get status of all configured channels."""
        status = {
            "total_channels": len(self.channels),
            "enabled_channels": sum(1 for c in self.channels.values() if c.enabled),
            "total_rules": len(self.rules),
            "total_deliveries": len(self.delivery_history),
            "failed_deliveries": sum(
                1
                for r in self.delivery_history
                if r.status == DeliveryStatus.FAILED
            ),
            "channels_by_type": {},
        }

        for channel_type in AlertChannel:
            count = sum(
                1
                for c in self.channels.values()
                if c.channel_type == channel_type and c.enabled
            )
            status["channels_by_type"][channel_type.value] = count

        return status


# Global instance
_alert_router: Optional[AlertChannelRouter] = None


def get_alert_router() -> AlertChannelRouter:
    """Get or create global alert channel router."""
    global _alert_router
    if _alert_router is None:
        _alert_router = AlertChannelRouter()
    return _alert_router
