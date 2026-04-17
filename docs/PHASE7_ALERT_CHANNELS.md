# Phase 7: Alert Channels - Email, Slack, PagerDuty Integration

**Project:** Policy-Aware AI Gateway - OpenClaw Agent Lab  
**Phase:** 7 (Alert Delivery Channels)  
**Status:** Week 1 Complete - Backend Implementation  
**Date Started:** April 16, 2026

---

## Overview

Phase 7 extends the real-time alert system to support delivery via multiple channels: **Email**, **Slack**, and **PagerDuty**. Users can now configure alert routing rules to send critical alerts directly to their communication platforms and incident management systems.

---

## Architecture

### Alert Channel Flow

```
Alert Generated (Phase 6)
    ↓
AlertTriggerEngine (evaluates triggers)
    ↓
AlertChannelRouter (routes to channels)
    ├─ EmailService
    ├─ SlackService
    └─ PagerDutyService
    ↓
AlertDeliveryRecord (tracks delivery)
    ↓
User Receives Notification
    (Email inbox, Slack channel, PagerDuty incident)
```

### Channel Architecture

```
Backend Services:
- AlertChannelConfig: Channel configuration (destination, enabled, filters)
- DeliveryRule: Routing rules (which alerts → which channels)
- AlertChannelRouter: Main router (manages channels, rules, delivery)
- EmailService: SMTP email delivery
- SlackService: Webhook-based Slack delivery
- PagerDutyService: API-based PagerDuty integration

Frontend Components:
- ChannelSettings: Configure channels (add, edit, remove, test)
- DeliveryRules: Configure routing rules (which alerts to which channels)
- DeliveryHistory: View delivery attempts and status

Database:
- alert_channels: Stored channel configurations
- delivery_rules: Stored routing rules
- delivery_history: Delivery attempt records (for audit trail)
```

---

## Week 1: Backend Implementation

### Services Implemented

#### 1. AlertChannelConfig
```python
@dataclass
class AlertChannelConfig:
    channel_type: AlertChannel  # email, slack, pagerduty
    enabled: bool
    destination: str  # email, webhook URL, or integration key
    include_critical: bool = True
    include_warning: bool = True
    include_info: bool = False
```

#### 2. DeliveryRule
```python
@dataclass
class DeliveryRule:
    trigger_type: str  # high_cost_query, slow_query, etc.
    channel_type: AlertChannel
    enabled: bool
    alert_levels: List[str] = ["critical", "warning"]
```

#### 3. AlertChannelRouter (Main Service)

**Capabilities:**
- Add/remove alert channels
- Create/modify delivery rules
- Route alerts to appropriate channels based on rules
- Track delivery history with retry logic
- Test channel connectivity

**Methods:**
```python
add_channel(config)                    # Register new channel
remove_channel(channel_type, dest)     # Remove channel
add_rule(rule)                         # Add routing rule
get_channels_for_alert(type, level)    # Get target channels
route_alert(alert_data)                # Route alert through channels
record_delivery(record)                # Record delivery attempt
test_channel(config)                   # Test channel configuration
get_channel_status()                   # Get overall status
```

#### 4. EmailService
- SMTP-based email delivery
- Formatted alert emails with subject, body, metadata
- Connection testing capability

#### 5. SlackService
- Webhook-based Slack integration
- Rich formatted messages with fields
- Color-coded by severity (Red=Critical, Orange=Warning, Blue=Info)
- Includes alert title, message, trigger value, threshold

#### 6. PagerDutyService
- API integration (v2 Events API)
- Creates incidents/alerts in PagerDuty
- Severity mapping (critical, warning, info)
- Custom details in incident body

### Test Coverage (Week 1)

**Backend Tests:** 40+ tests
- AlertChannelConfig: 4 tests
- DeliveryRule: 2 tests
- EmailService: 2 tests
- SlackService: 3 tests
- PagerDutyService: 2 tests
- AlertChannelRouter: 25+ tests
  - Channel management (add, remove, list)
  - Rule management (create, modify)
  - Alert routing by trigger and severity
  - Delivery history filtering
  - Channel testing
  - Status reporting

**All Week 1 tests passing** ✅

---

## Week 2: Frontend UI (Planned)

### Components

#### ChannelSettings Component
- Display configured channels
- Enable/disable channels
- Configure severity filters (critical, warning, info)
- Add new channels (email, Slack, PagerDuty)
- Remove channels
- Test channel connectivity

#### DeliveryRules Component
- Display active delivery rules
- Create new rules (trigger type + channel)
- Select alert levels (critical, warning, info)
- Enable/disable rules
- Remove rules
- Visual rule editor

#### DeliveryHistory Component
- List all delivery attempts
- Filter by status (sent, failed, pending, retrying)
- Expand for details (alert ID, timestamp, error)
- Retry failed deliveries
- Summary stats (successful, failed, pending)

### Frontend Tests (Planned)
- ChannelSettings: 15+ tests
- DeliveryRules: 12+ tests
- DeliveryHistory: 10+ tests
- useChannelSettings hook: 10+ tests
- Total: 50+ tests

---

## Week 3: Integration & Polish (Planned)

### Backend Integration
- Wire AlertChannelRouter into AlertTriggerEngine
- Integration with existing alert system
- Async delivery queue with retry logic
- Error handling and fallback

### Frontend Integration
- Dashboard settings page with both components
- Alert channel configuration UI
- Settings persistence to backend
- Real-time status updates

### Documentation
- User guide for configuring channels
- Developer API reference
- Setup guides for each platform (Gmail, Slack, PagerDuty)
- Troubleshooting guide

---

## Channel Setup Guides

### Email Configuration

**Requirements:**
- SMTP server (Gmail, SendGrid, etc.)
- Email address and password/app token

**Configuration (Backend):**
```python
email_service = EmailService(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="alerts@yourdomain.com",
    smtp_password="your-app-password"
)
```

**Configuration (Frontend):**
1. Go to Settings → Alert Channels
2. Click "+ Add Channel"
3. Select "Email"
4. Enter email address (e.g., alerts@yourdomain.com)
5. Click "Send Test" to verify
6. Configure severity filters (Critical, Warning, Info)
7. Save

### Slack Configuration

**Requirements:**
- Slack workspace
- Webhook URL from Slack app

**Getting Webhook URL:**
1. Go to https://api.slack.com/apps
2. Create new app or select existing
3. Enable Incoming Webhooks
4. Add New Webhook to Workspace
5. Copy Webhook URL

**Configuration (Frontend):**
1. Settings → Alert Channels
2. "+ Add Channel"
3. Select "Slack"
4. Paste webhook URL
5. "Send Test"
6. Set severity filters
7. Save

### PagerDuty Configuration

**Requirements:**
- PagerDuty account
- Integration key from event integration

**Getting Integration Key:**
1. Go to https://www.pagerduty.com
2. Services → Create Service (or select existing)
3. Integrations → + Create a new Events Integration
4. Select "Events API v2"
5. Copy integration key

**Configuration (Frontend):**
1. Settings → Alert Channels
2. "+ Add Channel"
3. Select "PagerDuty"
4. Paste integration key
5. "Send Test"
6. Set severity filters
7. Save

---

## Delivery Rules

### Rule Examples

**Example 1: High-Cost Alerts to Email**
- Trigger Type: `high_cost_query`
- Channel: Email (alerts@yourdomain.com)
- Alert Levels: Warning, Critical
- Effect: All high-cost alerts sent to email

**Example 2: Critical Errors to Slack + PagerDuty**
- Trigger Type: `error_spike`
- Channel: Slack #alerts
- Alert Levels: Critical
- Repeat for PagerDuty channel

**Example 3: Info Messages to None**
- Trigger Type: Any
- Include Info: False
- Effect: Info-level alerts not delivered externally

### Rule Configuration Flow

```
1. Configure Channel
   ↓
2. Add Delivery Rule
   - Select trigger type (high_cost, slow_query, etc.)
   - Select channel to deliver to
   - Select alert levels (critical, warning, info)
   - Save rule
   ↓
3. Rule is Active
   - Future alerts matching rule will be delivered
   - View delivery status in history
```

---

## API Reference (Backend)

### Add Channel Endpoint (Week 2)

```
POST /api/v1/alert-channels/channels

Body:
{
  "channel_type": "email|slack|pagerduty",
  "destination": "alerts@example.com",
  "enabled": true,
  "include_critical": true,
  "include_warning": true,
  "include_info": false
}

Response:
{
  "id": "channel-123",
  "channel_type": "email",
  ...
}
```

### Create Delivery Rule (Week 2)

```
POST /api/v1/alert-channels/rules

Body:
{
  "trigger_type": "high_cost_query",
  "channel_type": "email",
  "enabled": true,
  "alert_levels": ["critical", "warning"]
}

Response:
{
  "id": "rule-456",
  ...
}
```

### Get Delivery History (Week 2)

```
GET /api/v1/alert-channels/history?status=sent&limit=50

Response:
{
  "records": [
    {
      "id": "delivery-789",
      "alert_id": "alert-1",
      "channel_type": "email",
      "destination": "alerts@example.com",
      "status": "sent",
      "timestamp": "2026-04-16T10:30:00Z",
      "retry_count": 0
    }
  ],
  "total": 100
}
```

### Test Channel (Week 2)

```
POST /api/v1/alert-channels/test

Body:
{
  "channel_type": "slack",
  "destination": "https://hooks.slack.com/..."
}

Response:
{
  "success": true,
  "message": "Test alert sent successfully"
}
```

---

## Delivery Guarantee

### Retry Logic

- **First Attempt**: Immediate delivery
- **Retry 1**: After 1 minute (if failed)
- **Retry 2**: After 5 minutes (if failed)
- **Retry 3**: After 15 minutes (if failed)
- **Give Up**: After 3 retries, mark as failed

### Failure Scenarios

**Network Error:**
- Retry with exponential backoff
- Max 3 retries

**Invalid Configuration:**
- Immediate failure
- No retry
- Display error in delivery history

**Rate Limiting:**
- Retry with delay
- Backoff respected

---

## Error Handling

### Email Delivery Errors
- SMTP connection failed → retry
- Invalid email format → fail, no retry
- Authentication failed → fail, no retry

### Slack Delivery Errors
- Webhook URL invalid → fail, no retry
- Network error → retry
- Slack service error → retry

### PagerDuty Delivery Errors
- Invalid integration key → fail, no retry
- API error → retry
- Rate limit → retry with backoff

---

## Security Considerations

✅ **API Keys/Tokens**
- Store securely in environment variables
- Never log full keys
- Rotate regularly

✅ **Webhook URLs**
- Encrypt at rest
- Verify HTTPS
- Validate URL format

✅ **Access Control**
- User can only manage their own channels
- Admin can view all channels/rules
- Audit trail of configuration changes

✅ **Data Privacy**
- Alert content in logs (if needed)
- Redact sensitive values
- Compliance with data retention policies

---

## Performance Characteristics

### Delivery Latency

| Channel | Latency | Notes |
|---------|---------|-------|
| Email | 1-5 seconds | SMTP may vary by provider |
| Slack | 500ms-2s | Webhook-based, usually fast |
| PagerDuty | 1-3 seconds | API-based |

### Throughput

- **Email**: 10+ emails/sec (depends on SMTP provider)
- **Slack**: 50+ webhooks/sec (depends on rate limit)
- **PagerDuty**: 100+ events/sec

### Reliability

- **Retry Logic**: Exponential backoff up to 3 attempts
- **Delivery Guarantee**: Best-effort with retry
- **Success Rate Target**: >99% for valid configurations

---

## Monitoring & Debugging

### Delivery Status Indicators

**In Delivery History:**
- ✓ Sent: Successfully delivered
- ✗ Failed: All retries exhausted
- ⏳ Pending: Queued for delivery
- 🔄 Retrying: Retry in progress

### Debug Information

**Per Delivery Record:**
- Alert ID that triggered delivery
- Channel type and destination
- Timestamp of attempt
- Status code/error message
- Retry count (e.g., 1/3)

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Email not received | SMTP config | Verify credentials, check spam |
| Slack webhook fails | Webhook expired | Regenerate webhook URL |
| PagerDuty no incidents | Invalid key | Verify integration key |
| Delays | Rate limiting | Check provider rate limits |

---

## Testing Deliveries

### Manual Testing

**Per Channel:**
1. Settings → Alert Channels
2. Scroll to channel
3. Click "Send Test"
4. Wait for result
5. Check external service (email inbox, Slack, PagerDuty)

### Automated Testing

**E2E Test Flow:**
1. Create test channel
2. Create test rule
3. Trigger matching alert
4. Verify delivery in history
5. Check external service
6. Verify delivery status = "sent"
7. Clean up

---

## Future Enhancements (Phase 8+)

1. **Webhook Delivery** - Send to custom webhooks
2. **SMS Alerts** - Text message delivery (Twilio)
3. **Microsoft Teams** - Teams webhook integration
4. **Discord** - Discord channel alerts
5. **Alert Escalation** - Automatic escalation to higher severity
6. **Scheduled Digests** - Batch alerts (hourly, daily)
7. **Bi-Directional** - Acknowledge alerts from Slack/Teams
8. **Webhook Signatures** - HMAC-based security

---

## Implementation Checklist

### Week 1 - Backend ✅
- [x] AlertChannelConfig dataclass
- [x] DeliveryRule dataclass
- [x] EmailService implementation
- [x] SlackService implementation
- [x] PagerDutyService implementation
- [x] AlertChannelRouter implementation
- [x] AlertDeliveryRecord model
- [x] 40+ backend tests

### Week 2 - Frontend (In Progress)
- [ ] ChannelSettings component
- [ ] DeliveryRules component
- [ ] DeliveryHistory component
- [ ] useChannelSettings hook
- [ ] API client methods
- [ ] 50+ frontend tests
- [ ] Integration with settings page

### Week 3 - Integration & Polish
- [ ] Wire AlertChannelRouter into alert system
- [ ] Async delivery queue
- [ ] Retry logic implementation
- [ ] Settings persistence
- [ ] E2E testing
- [ ] Complete documentation
- [ ] Deployment guide

---

**Phase 7 Status: Week 1 Complete ✅**

Backend infrastructure implemented with 40+ tests passing. Ready for Week 2 frontend implementation.
