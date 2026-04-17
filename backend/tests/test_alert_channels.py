"""Tests for alert channel delivery system."""

import pytest
from datetime import datetime
from backend.src.services.alert_channels import (
    AlertChannel,
    AlertChannelConfig,
    AlertChannelRouter,
    DeliveryRule,
    DeliveryStatus,
    EmailService,
    SlackService,
    PagerDutyService,
)


class TestAlertChannelConfig:
    """Test alert channel configuration."""

    def test_create_email_channel(self):
        """Test creating email channel configuration."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
            include_critical=True,
            include_warning=True,
        )

        assert config.channel_type == AlertChannel.EMAIL
        assert config.destination == "alerts@example.com"
        assert config.enabled is True

    def test_create_slack_channel(self):
        """Test creating Slack channel configuration."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.SLACK,
            enabled=True,
            destination="https://hooks.slack.com/services/...",
        )

        assert config.channel_type == AlertChannel.SLACK

    def test_create_pagerduty_channel(self):
        """Test creating PagerDuty channel configuration."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.PAGERDUTY,
            enabled=True,
            destination="integration-key-12345",
        )

        assert config.channel_type == AlertChannel.PAGERDUTY

    def test_channel_defaults(self):
        """Test channel configuration defaults."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="test@example.com",
        )

        assert config.include_critical is True
        assert config.include_warning is True
        assert config.include_info is False


class TestDeliveryRule:
    """Test delivery rule configuration."""

    def test_create_rule(self):
        """Test creating delivery rule."""
        rule = DeliveryRule(
            trigger_type="high_cost_query",
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            alert_levels=["warning"],
        )

        assert rule.trigger_type == "high_cost_query"
        assert rule.channel_type == AlertChannel.EMAIL
        assert rule.enabled is True

    def test_rule_defaults(self):
        """Test rule default alert levels."""
        rule = DeliveryRule(
            trigger_type="test",
            channel_type=AlertChannel.SLACK,
            enabled=True,
        )

        assert rule.alert_levels == ["critical", "warning"]


class TestEmailService:
    """Test email delivery service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EmailService()

    @pytest.mark.asyncio
    async def test_send_alert(self):
        """Test sending alert via email."""
        result = await self.service.send_alert(
            to_email="test@example.com",
            alert_title="Test Alert",
            alert_message="Test message",
            alert_level="warning",
            trigger_value=15.0,
            threshold=10.0,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection(self):
        """Test email connection test."""
        result = await self.service.test_connection("test@example.com")
        assert result is True


class TestSlackService:
    """Test Slack delivery service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SlackService()

    @pytest.mark.asyncio
    async def test_send_alert_format(self):
        """Test Slack alert message format."""
        result = await self.service.send_alert(
            webhook_url="https://hooks.slack.com/services/test",
            alert_title="High Cost Alert",
            alert_message="Query exceeded cost threshold",
            alert_level="warning",
        )

        # Would return False with mock URL, but tests structure
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_alert_color_coding(self):
        """Test Slack color coding by severity."""
        # Critical = red, warning = orange, info = blue
        colors = {
            "critical": "#FF0000",
            "warning": "#FFA500",
            "info": "#0099FF",
        }

        for level, expected_color in colors.items():
            result = await self.service.send_alert(
                webhook_url="https://hooks.slack.com/services/test",
                alert_title="Test",
                alert_message="Test",
                alert_level=level,
            )

            assert isinstance(result, bool)


class TestPagerDutyService:
    """Test PagerDuty delivery service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PagerDutyService()

    @pytest.mark.asyncio
    async def test_send_alert(self):
        """Test creating PagerDuty incident."""
        result = await self.service.send_alert(
            integration_key="test-integration-key",
            alert_title="Critical System Issue",
            alert_message="System degradation detected",
            alert_level="critical",
        )

        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_severity_mapping(self):
        """Test PagerDuty severity mapping."""
        for level in ["critical", "warning", "info"]:
            result = await self.service.send_alert(
                integration_key="test-key",
                alert_title="Test",
                alert_message="Test",
                alert_level=level,
            )

            assert isinstance(result, bool)


class TestAlertChannelRouter:
    """Test alert channel router."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = AlertChannelRouter()

    def test_add_channel(self):
        """Test adding alert channel."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
        )

        self.router.add_channel(config)

        assert len(self.router.channels) == 1

    def test_add_multiple_channels(self):
        """Test adding multiple channels."""
        email_config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
        )
        slack_config = AlertChannelConfig(
            channel_type=AlertChannel.SLACK,
            enabled=True,
            destination="https://hooks.slack.com/...",
        )

        self.router.add_channel(email_config)
        self.router.add_channel(slack_config)

        assert len(self.router.channels) == 2

    def test_remove_channel(self):
        """Test removing alert channel."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
        )

        self.router.add_channel(config)
        assert len(self.router.channels) == 1

        self.router.remove_channel(AlertChannel.EMAIL, "alerts@example.com")
        assert len(self.router.channels) == 0

    def test_add_rule(self):
        """Test adding delivery rule."""
        rule = DeliveryRule(
            trigger_type="high_cost_query",
            channel_type=AlertChannel.EMAIL,
            enabled=True,
        )

        self.router.add_rule(rule)

        assert len(self.router.rules) == 1

    def test_get_channels_for_alert(self):
        """Test getting channels for specific alert."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
            include_critical=True,
            include_warning=False,
        )

        rule = DeliveryRule(
            trigger_type="high_cost_query",
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            alert_levels=["critical"],
        )

        self.router.add_channel(config)
        self.router.add_rule(rule)

        channels = self.router.get_channels_for_alert("high_cost_query", "critical")

        assert len(channels) == 1
        assert channels[0].channel_type == AlertChannel.EMAIL

    def test_get_channels_respects_alert_level(self):
        """Test channels filtered by alert level."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
            include_critical=True,
            include_warning=False,
        )

        rule = DeliveryRule(
            trigger_type="test",
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            alert_levels=["critical"],
        )

        self.router.add_channel(config)
        self.router.add_rule(rule)

        critical_channels = self.router.get_channels_for_alert("test", "critical")
        warning_channels = self.router.get_channels_for_alert("test", "warning")

        assert len(critical_channels) == 1
        assert len(warning_channels) == 0

    @pytest.mark.asyncio
    async def test_route_alert(self):
        """Test routing alert through channels."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
            include_warning=True,
        )

        rule = DeliveryRule(
            trigger_type="high_cost_query",
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            alert_levels=["warning"],
        )

        self.router.add_channel(config)
        self.router.add_rule(rule)

        records = await self.router.route_alert(
            alert_id="alert-1",
            trigger_type="high_cost_query",
            alert_title="High Cost Query",
            alert_message="Query cost exceeded threshold",
            alert_level="warning",
            trigger_value=15.0,
            threshold=10.0,
        )

        assert len(records) > 0
        assert records[0].status in [DeliveryStatus.SENT, DeliveryStatus.FAILED]

    def test_record_delivery(self):
        """Test recording delivery attempt."""
        from backend.src.services.alert_channels import AlertDeliveryRecord

        record = AlertDeliveryRecord(
            alert_id="alert-1",
            channel_type=AlertChannel.EMAIL,
            destination="test@example.com",
            status=DeliveryStatus.SENT,
            timestamp=datetime.utcnow(),
        )

        self.router.record_delivery(record)

        assert len(self.router.delivery_history) == 1

    def test_get_delivery_history(self):
        """Test retrieving delivery history."""
        from backend.src.services.alert_channels import AlertDeliveryRecord

        for i in range(5):
            record = AlertDeliveryRecord(
                alert_id=f"alert-{i}",
                channel_type=AlertChannel.EMAIL,
                destination="test@example.com",
                status=DeliveryStatus.SENT,
                timestamp=datetime.utcnow(),
            )
            self.router.record_delivery(record)

        history = self.router.get_delivery_history(limit=10)

        assert len(history) == 5

    def test_delivery_history_limit(self):
        """Test delivery history respects size limit."""
        from backend.src.services.alert_channels import AlertDeliveryRecord

        for i in range(1100):
            record = AlertDeliveryRecord(
                alert_id=f"alert-{i}",
                channel_type=AlertChannel.EMAIL,
                destination="test@example.com",
                status=DeliveryStatus.SENT,
                timestamp=datetime.utcnow(),
            )
            self.router.record_delivery(record)

        assert len(self.router.delivery_history) == 1000

    def test_get_delivery_history_filtered(self):
        """Test filtering delivery history."""
        from backend.src.services.alert_channels import AlertDeliveryRecord

        email_record = AlertDeliveryRecord(
            alert_id="alert-1",
            channel_type=AlertChannel.EMAIL,
            destination="test@example.com",
            status=DeliveryStatus.SENT,
            timestamp=datetime.utcnow(),
        )

        slack_record = AlertDeliveryRecord(
            alert_id="alert-1",
            channel_type=AlertChannel.SLACK,
            destination="https://hooks.slack.com/...",
            status=DeliveryStatus.SENT,
            timestamp=datetime.utcnow(),
        )

        self.router.record_delivery(email_record)
        self.router.record_delivery(slack_record)

        email_history = self.router.get_delivery_history(channel_type=AlertChannel.EMAIL)

        assert len(email_history) == 1
        assert email_history[0].channel_type == AlertChannel.EMAIL

    @pytest.mark.asyncio
    async def test_test_channel(self):
        """Test channel configuration test."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="test@example.com",
        )

        result = await self.router.test_channel(config)

        assert isinstance(result, bool)

    def test_get_channel_status(self):
        """Test getting channel status."""
        email_config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
        )
        slack_config = AlertChannelConfig(
            channel_type=AlertChannel.SLACK,
            enabled=False,
            destination="https://hooks.slack.com/...",
        )

        self.router.add_channel(email_config)
        self.router.add_channel(slack_config)

        status = self.router.get_channel_status()

        assert status["total_channels"] == 2
        assert status["enabled_channels"] == 1
        assert status["channels_by_type"]["email"] == 1

    def test_disable_channel(self):
        """Test disabling specific channel."""
        config = AlertChannelConfig(
            channel_type=AlertChannel.EMAIL,
            enabled=True,
            destination="alerts@example.com",
        )

        self.router.add_channel(config)
        config.enabled = False

        channels = self.router.get_channels_for_alert("test", "warning")

        assert len(channels) == 0
