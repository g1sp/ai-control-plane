# Phase 2 API Reference

**Version:** 2.0.0  
**Gateway:** Policy-Aware AI Gateway with Agent Orchestration  
**Date:** April 16, 2026

---

## Overview

Phase 2 introduces 6 new API endpoints for agent orchestration, tool management, and approval workflows. All endpoints are production-ready with complete error handling and audit logging.

### Base URL
```
http://localhost:8000
```

### Authentication
Currently no authentication required (Phase 3 enhancement). Relies on PolicyEngine user validation.

---

## 1. Execute Agent

**Endpoint:** `POST /agent/run`

**Description:** Execute an agent with tool calling capability. The agent will reason, call tools as needed, and return results with full execution trace.

### Request

```json
{
  "goal": "What's the weather in New York?",
  "user_id": "alice@company.com",
  "budget_usd": 0.50,
  "context": {
    "location": "New York",
    "format": "celsius"
  },
  "max_iterations": 10,
  "timeout_seconds": 60
}
```

### Parameters

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-----------|-------------|
| goal | string | Yes | - | 1-10000 chars | Task for agent to accomplish |
| user_id | string | Yes | - | Email format | User requesting agent execution |
| budget_usd | number | Yes | - | 0.001 - 1000 | Cost limit in USD |
| context | object | No | {} | JSON | Additional context for agent |
| max_iterations | integer | No | 10 | 1-50 | Maximum reasoning iterations |
| timeout_seconds | integer | No | 60 | 5-600 | Execution timeout |

### Response

**Status:** 200 OK

```json
{
  "agent_id": "agent_abc123xyz",
  "request_id": "req_xyz789abc",
  "user_id": "alice@company.com",
  "goal": "What's the weather in New York?",
  "status": "completed",
  "final_response": "Based on the search results, New York currently has...",
  "execution_trace": [
    {
      "type": "thinking",
      "content": "I need to search for weather information...",
      "duration_ms": 150
    },
    {
      "type": "tool_call",
      "content": "Called search with args: {\"query\": \"New York weather\"}",
      "tool_call": {
        "name": "search",
        "args": {"query": "New York weather"},
        "timestamp": "2026-04-16T12:30:45Z"
      },
      "duration_ms": 250
    }
  ],
  "tools_called": [
    {
      "name": "search",
      "args": {"query": "New York weather"},
      "timestamp": "2026-04-16T12:30:45Z"
    }
  ],
  "total_cost_usd": 0.015,
  "duration_ms": 1250,
  "error_message": null,
  "timestamp": "2026-04-16T12:30:47Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| agent_id | string | Unique agent execution ID |
| request_id | string | Request correlation ID |
| user_id | string | User who made request |
| goal | string | Original task goal |
| status | string | "completed", "failed", or "timeout" |
| final_response | string | Agent's final answer |
| execution_trace | array | Step-by-step execution details |
| tools_called | array | List of all tools called |
| total_cost_usd | number | Total cost in USD |
| duration_ms | number | Total execution time |
| error_message | string | Error details if failed |
| timestamp | string | ISO 8601 timestamp |

### Error Responses

**403 Forbidden - Policy Violation**
```json
{
  "error": "policy_violation",
  "reason": "User not in whitelist",
  "request_id": "req_xyz789abc"
}
```

**503 Service Unavailable - Execution Failed**
```json
{
  "error": "agent_execution_failed",
  "reason": "Claude API unavailable",
  "request_id": "req_xyz789abc"
}
```

---

## 2. Get Execution History

**Endpoint:** `GET /agent/executions`

**Description:** Query agent execution history for a user within a time window.

### Request

```bash
GET /agent/executions?user=alice@company.com&hours=24&limit=10
```

### Parameters

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-----------|-------------|
| user | string | Yes | - | Email | User to query |
| hours | integer | No | 24 | 1-168 | Time window in hours |
| limit | integer | No | 100 | 1-1000 | Max results |

### Response

**Status:** 200 OK

```json
{
  "user_id": "alice@company.com",
  "total_executions": 3,
  "total_cost_usd": 0.045,
  "executions": [
    {
      "agent_id": "agent_abc123",
      "request_id": "req_123",
      "goal": "What's the weather?",
      "status": "completed",
      "total_cost_usd": 0.015,
      "duration_ms": 1250,
      "timestamp": "2026-04-16T12:30:47Z"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User queried |
| total_executions | integer | Count of executions |
| total_cost_usd | number | Sum of all costs |
| executions | array | Execution summaries |

---

## 3. List Pending Approvals

**Endpoint:** `GET /agent/approvals`

**Description:** List all pending tool approval requests awaiting admin action.

### Request

```bash
GET /agent/approvals
```

### Response

**Status:** 200 OK

```json
{
  "total_pending": 2,
  "approvals": [
    {
      "approval_id": "appr_123abc",
      "user_id": "user@example.com",
      "tool_name": "python_eval",
      "args": {"code": "2 + 2"},
      "created_at": "2026-04-16T12:00:00Z",
      "status": "pending"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| total_pending | integer | Count pending approvals |
| approvals | array | Approval requests |

---

## 4. Approve/Reject Tool Execution

**Endpoint:** `POST /agent/approve/{approval_id}`

**Description:** Approve or reject a pending tool execution request.

### Request

```json
{
  "decision": "approve",
  "reason": "Verified code is safe"
}
```

### Parameters

| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| decision | string | Yes | "approve", "reject" | Approval decision |
| reason | string | No | - | Justification |

### Response

**Status:** 200 OK

```json
{
  "approval_id": "appr_123abc",
  "decision": "approve",
  "reason": "Verified code is safe",
  "status": "processed"
}
```

### Error Responses

**404 Not Found**
```json
{
  "detail": "Approval not found"
}
```

---

## 5. List Available Tools

**Endpoint:** `GET /tools`

**Description:** List all available tools with metadata and execution requirements.

### Request

```bash
GET /tools
```

### Response

**Status:** 200 OK

```json
{
  "total_tools": 3,
  "tools": [
    {
      "name": "http_get",
      "description": "Make HTTP GET requests",
      "enabled": true,
      "requires_approval": false,
      "input_schema": {
        "type": "object",
        "properties": {
          "url": {"type": "string", "description": "URL to fetch"},
          "headers": {"type": "object", "description": "Optional headers"}
        },
        "required": ["url"]
      }
    },
    {
      "name": "python_eval",
      "description": "Execute Python code safely",
      "enabled": true,
      "requires_approval": true,
      "input_schema": {
        "type": "object",
        "properties": {
          "code": {"type": "string", "description": "Python code to execute"}
        },
        "required": ["code"]
      }
    },
    {
      "name": "search",
      "description": "Search for information",
      "enabled": true,
      "requires_approval": false,
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "Search query"},
          "limit": {"type": "integer", "description": "Max results"}
        },
        "required": ["query"]
      }
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| total_tools | integer | Count of tools |
| tools | array | Tool definitions |
| tools[].name | string | Tool identifier |
| tools[].description | string | Tool purpose |
| tools[].enabled | boolean | Tool availability |
| tools[].requires_approval | boolean | Approval gate |
| tools[].input_schema | object | JSON schema |

---

## Common Error Codes

### 400 Bad Request
Invalid request parameters
```json
{"detail": "Invalid budget value"}
```

### 403 Forbidden
Policy violation or access denied
```json
{"error": "policy_violation", "reason": "User not authorized"}
```

### 404 Not Found
Resource not found
```json
{"detail": "Resource not found"}
```

### 503 Service Unavailable
Gateway or upstream service error
```json
{"error": "execution_failed", "reason": "Service unavailable"}
```

---

## Rate Limits

All endpoints are rate limited per user:

| Resource | Limit | Window |
|----------|-------|--------|
| `/agent/run` | 10 requests | Per minute |
| `/agent/run` | 100 requests | Per day |
| `/tools` | 100 requests | Per minute |

Exceeding limits returns `429 Too Many Requests`

---

## Cost Model

Costs are calculated per Claude API call:

| Model | Input Cost | Output Cost |
|-------|-----------|-----------|
| claude-sonnet-4-6 | $0.003 per 1K tokens | $0.015 per 1K tokens |
| claude-haiku | $0.00008 per 1K tokens | $0.0004 per 1K tokens |

Budget enforcement:
- Pre-execution check: Estimated cost vs budget
- Runtime check: Actual tokens vs budget
- Execution stops if budget exceeded

---

## Examples

### Example 1: Simple Query

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "What is 2 + 2?",
    "user_id": "user@example.com",
    "budget_usd": 0.10
  }'
```

### Example 2: Search with Context

```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Find the latest news about AI safety",
    "user_id": "researcher@example.com",
    "budget_usd": 0.50,
    "context": {
      "max_results": 5,
      "time_range": "1_week"
    }
  }'
```

### Example 3: Check Approvals

```bash
curl http://localhost:8000/agent/approvals

# Response shows pending approvals for admin review
```

---

## Integration Notes

- All endpoints log to audit trail via AuditLogger
- Cost tracking integrated with CostCalculator
- Policy validation via PolicyEngine
- User whitelist enforced on all agent endpoints
- Tool execution gated by approval workflow when required
