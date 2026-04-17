# Phase 3: Real-Time Streaming Guide

**Version:** 3.0.0 (Phase 3 Week 1)  
**Status:** Production Ready  
**Date:** April 16, 2026

---

## Overview

Phase 3 introduces real-time streaming for agent execution. Watch agent reasoning, tool calls, and cost updates as they happen via WebSocket or Server-Sent Events (SSE).

**Key Features:**
- ✅ WebSocket streaming (recommended for high performance)
- ✅ SSE fallback (for simpler clients/browsers)
- ✅ Real-time token and cost tracking
- ✅ Tool execution visibility
- ✅ Complete execution history

---

## Quick Start

### Create Streaming Session

```bash
curl -X POST "http://localhost:8000/agent/stream/session?user_id=user@example.com&goal=What%20is%202%2B2?"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user@example.com",
  "goal": "What is 2+2?",
  "status": "created",
  "timestamp": "2026-04-16T12:00:00Z"
}
```

### Connect via WebSocket

```javascript
const sessionId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/agent/stream/${sessionId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`[${message.type}] ${message.content}`);
  // Display progress to user
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## API Endpoints

### 1. Create Streaming Session

**Endpoint:** `POST /agent/stream/session`

**Parameters:**
- `user_id` (string, required) - User email
- `goal` (string, required) - Task description

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": "user@example.com",
  "goal": "Task description",
  "status": "created",
  "timestamp": "ISO 8601"
}
```

---

### 2. WebSocket Streaming (Recommended)

**Endpoint:** `GET /agent/stream/{session_id}` (WebSocket)

**Connection:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/agent/stream/${sessionId}`);
```

**Events Received:**
```json
{
  "type": "thinking|tool_call|tool_result|cost_update|error|complete",
  "timestamp": "ISO 8601",
  "content": "Human-readable message",
  "data": {
    "tool": "tool_name",
    "args": {},
    "cost_usd": 0.015
  }
}
```

**Event Types:**

| Type | Meaning | Data |
|------|---------|------|
| `thinking` | Agent reasoning | None |
| `tool_call` | Calling a tool | `tool`, `args` |
| `tool_result` | Tool returned result | `tool`, `result` |
| `cost_update` | Cost/token update | `tokens_in`, `tokens_out`, `cost_usd` |
| `error` | Error occurred | `error` message |
| `complete` | Agent finished | `cost_usd`, final response |

**Reconnection:**
```javascript
const connectWithRetry = () => {
  const ws = new WebSocket(`ws://localhost:8000/agent/stream/${sessionId}`);
  
  ws.onerror = () => {
    console.log("Reconnecting in 3s...");
    setTimeout(connectWithRetry, 3000);
  };
};
```

---

### 3. Server-Sent Events (SSE) Fallback

**Endpoint:** `GET /agent/stream/{session_id}/sse`

**Connection:**
```javascript
const eventSource = new EventSource(`/agent/stream/${sessionId}/sse`);

eventSource.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

**Response Format:** Server-Sent Events (one JSON per line)
```
data: {"type":"thinking","content":"...","timestamp":"..."}

data: {"type":"tool_call","content":"...","data":{...}}

data: {"type":"complete","content":"...","data":{"cost_usd":0.015}}
```

---

### 4. Get Session Status

**Endpoint:** `GET /agent/stream/{session_id}/status`

**Response:**
```json
{
  "session_id": "uuid",
  "completed": false,
  "total_events": 5,
  "total_cost_usd": 0.015,
  "final_response": null,
  "created_at": "ISO 8601",
  "duration_seconds": 2.5
}
```

---

### 5. Get Session History

**Endpoint:** `GET /agent/stream/{session_id}/history`

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": "user@example.com",
  "goal": "What is 2+2?",
  "created_at": "ISO 8601",
  "completed": true,
  "final_response": "The answer is 4",
  "total_cost_usd": 0.015,
  "events": [
    {
      "type": "thinking",
      "timestamp": "ISO 8601",
      "content": "This is a math problem",
      "data": null
    },
    {
      "type": "tool_call",
      "timestamp": "ISO 8601",
      "content": "Calling python_eval",
      "data": {"tool": "python_eval", "args": {"code": "2 + 2"}}
    },
    {
      "type": "cost_update",
      "timestamp": "ISO 8601",
      "content": "Cost: $0.0005",
      "data": {"tokens_in": 50, "tokens_out": 10, "cost_usd": 0.0005}
    },
    {
      "type": "complete",
      "timestamp": "ISO 8601",
      "content": "The answer is 4",
      "data": {"cost_usd": 0.015}
    }
  ]
}
```

---

## JavaScript Client Library

Simple wrapper for easier integration:

```javascript
class StreamingAgent {
  constructor(apiBase = 'http://localhost:8000') {
    this.apiBase = apiBase;
  }

  async createSession(userId, goal) {
    const response = await fetch(
      `${this.apiBase}/agent/stream/session?user_id=${encodeURIComponent(userId)}&goal=${encodeURIComponent(goal)}`,
      { method: 'POST' }
    );
    return response.json();
  }

  connectWebSocket(sessionId, handlers) {
    const wsUrl = `ws://localhost:8000/agent/stream/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (handlers[message.type]) {
        handlers[message.type](message);
      }
    };

    ws.onerror = handlers.error || (() => {});
    return ws;
  }

  async getStatus(sessionId) {
    const response = await fetch(`${this.apiBase}/agent/stream/${sessionId}/status`);
    return response.json();
  }

  async getHistory(sessionId) {
    const response = await fetch(`${this.apiBase}/agent/stream/${sessionId}/history`);
    return response.json();
  }
}

// Usage
const agent = new StreamingAgent();

const session = await agent.createSession('user@example.com', 'What is the capital of France?');

agent.connectWebSocket(session.session_id, {
  thinking: (msg) => console.log('🤔', msg.content),
  tool_call: (msg) => console.log('🔧', msg.data.tool),
  tool_result: (msg) => console.log('✅', msg.content),
  cost_update: (msg) => console.log('💰', msg.content),
  complete: (msg) => console.log('🎉', msg.content),
  error: (msg) => console.error('❌', msg),
});
```

---

## Web UI Example

Simple HTML + JavaScript for streaming demo:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Agent Streaming Demo</title>
  <style>
    body { font-family: monospace; max-width: 800px; margin: 50px auto; }
    .event { padding: 8px; margin: 4px 0; border-left: 3px solid #ccc; }
    .thinking { border-color: #ffc107; background: #fff9e6; }
    .tool_call { border-color: #17a2b8; background: #e7f3ff; }
    .tool_result { border-color: #28a745; background: #e6ffe6; }
    .cost_update { border-color: #6c757d; background: #f0f0f0; }
    .complete { border-color: #28a745; background: #e6ffe6; font-weight: bold; }
    .error { border-color: #dc3545; background: #ffe6e6; }
    input { width: 100%; padding: 10px; font-size: 14px; }
    button { padding: 10px 20px; font-size: 14px; cursor: pointer; }
    #status { margin: 20px 0; padding: 10px; background: #f0f0f0; }
  </style>
</head>
<body>
  <h1>Agent Streaming Demo</h1>
  
  <input type="text" id="goal" placeholder="What do you want to ask?" value="What is 2+2?">
  <button onclick="startStream()">Start</button>
  
  <div id="status">Ready...</div>
  <div id="events"></div>

  <script src="streaming-client.js"></script>
  <script>
    const agent = new StreamingAgent();

    async function startStream() {
      const goal = document.getElementById('goal').value;
      const session = await agent.createSession('demo@example.com', goal);
      
      document.getElementById('status').textContent = `Session: ${session.session_id}`;
      document.getElementById('events').innerHTML = '';

      agent.connectWebSocket(session.session_id, {
        thinking: (msg) => addEvent('thinking', msg.content),
        tool_call: (msg) => addEvent('tool_call', `🔧 ${msg.data.tool}`),
        tool_result: (msg) => addEvent('tool_result', msg.content),
        cost_update: (msg) => addEvent('cost_update', msg.content),
        complete: (msg) => addEvent('complete', msg.content),
        error: (msg) => addEvent('error', msg.content),
      });
    }

    function addEvent(type, content) {
      const div = document.createElement('div');
      div.className = `event ${type}`;
      div.textContent = content;
      document.getElementById('events').appendChild(div);
      div.scrollIntoView();
    }
  </script>
</body>
</html>
```

---

## Performance

### Latency
- Event emission: <1ms
- WebSocket delivery: <10ms
- SSE delivery: <50ms
- Session lookup: <1ms

### Throughput
- 100 events/second per session
- Supports 100+ concurrent sessions on standard server

### Resource Usage
- ~1MB per session (in memory)
- No database I/O for events
- Sessions auto-cleanup after completion

---

## Error Handling

### Connection Errors

```javascript
ws.onerror = () => {
  console.error("Connection lost");
  reconnect(); // Implement retry logic
};

ws.onclose = () => {
  console.log("Stream ended");
};
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 101 | WebSocket upgrade successful |
| 200 | SSE stream started |
| 404 | Session not found |
| 503 | Server error |

---

## Deployment

### Nginx Configuration (Streaming)

```nginx
upstream gateway {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.example.com;

    # WebSocket upgrade
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    location /agent/stream {
        proxy_pass http://gateway;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;  # 24h timeout
    }

    location / {
        proxy_pass http://gateway;
        proxy_set_header Host $host;
    }
}
```

### Docker Configuration

```yaml
services:
  gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - STREAMING_MAX_SESSIONS=1000
      - STREAMING_SESSION_TTL=3600
```

---

## Testing

### Test WebSocket Connection

```bash
# Using wscat (npm install -g wscat)
wscat -c ws://localhost:8000/agent/stream/SESSION_ID
```

### Test SSE Connection

```bash
curl --stream http://localhost:8000/agent/stream/SESSION_ID/sse
```

### Load Testing

```bash
# Simulate 100 concurrent streaming sessions
ab -n 100 -c 100 http://localhost:8000/agent/stream/test/status
```

---

## Migration from Phase 2

**Phase 2** used `/agent/run` for synchronous execution.  
**Phase 3** adds streaming via `/agent/stream/session`.

Both work simultaneously - no breaking changes.

```javascript
// Phase 2: Synchronous
const response = await fetch('/agent/run', {
  method: 'POST',
  body: JSON.stringify({ goal, user_id, budget_usd })
});

// Phase 3: Streaming (New!)
const session = await fetch('/agent/stream/session?user_id=...&goal=...');
const ws = new WebSocket(`ws://localhost:8000/agent/stream/${sessionId}`);
```

---

## FAQ

**Q: WebSocket vs SSE - which should I use?**  
A: WebSocket is faster and bidirectional (future capability). Use SSE only if WebSocket not available.

**Q: How long do sessions persist?**  
A: In-memory, until marked complete. Cleanup happens after completion.

**Q: Can I stream to multiple clients?**  
A: Yes, multiple WebSocket clients can subscribe to same session.

**Q: What about network interruptions?**  
A: Session persists. Reconnect with same session_id to resume.

---

## Support

- Documentation: `docs/PHASE3_STREAMING_GUIDE.md`
- Issues: GitHub Issues
- Examples: `examples/streaming-client.js`
