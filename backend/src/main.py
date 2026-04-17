"""FastAPI application for Policy-Aware AI Gateway."""

import time
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .config import settings
from .database import init_db, get_db
from .models import (
    QueryRequest, QueryResponse, ErrorResponse, HealthResponse,
    AgentRequestBody, AgentExecutionResponse, AgentExecutionHistoryResponse,
    PendingApprovalsResponse, ApprovalDecisionRequest, ToolsListResponse, ToolInfo
)
from .services.policy import PolicyEngine
from .services.router import ModelRouter
from .services.audit import AuditLogger
from .services.cost_calculator import CostCalculator
from .services.streaming import get_stream_manager, StreamingEventCallback
from .integrations.ollama import OllamaClient
from .integrations.claude import ClaudeClient
from .utils.logger import logger
from .agents.engine import AgentExecutor
from .agents.models import AgentRequest as AgentRequestModel
from .tools.registry import ToolRegistry
from .policies.approval import ToolApprovalEngine
from .policies.restrictions import ToolRestrictionsManager

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Policy-Aware AI Gateway",
    description="Centralized control plane for AI requests",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients (initialized on first use)
ollama_client = None
claude_client = None
tool_registry = None
agent_executor = None
restrictions_manager = None
app_start_time = datetime.utcnow()


def get_ollama_client():
    """Get or initialize Ollama client."""
    global ollama_client
    if ollama_client is None:
        ollama_client = OllamaClient()
    return ollama_client


def get_claude_client():
    """Get or initialize Claude client."""
    global claude_client
    if claude_client is None:
        try:
            claude_client = ClaudeClient()
        except ValueError:
            # API key not set, will fail on use
            pass
    return claude_client


def get_tool_registry():
    """Get or initialize tool registry."""
    global tool_registry
    if tool_registry is None:
        from .tools.executors import HttpToolExecutor, PythonToolExecutor, SearchToolExecutor

        tool_registry = ToolRegistry()

        # Register built-in tools
        tool_registry.register(
            name="http_get",
            func=HttpToolExecutor.http_get,
            description="Make HTTP GET requests",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "headers": {"type": "object", "description": "Optional headers"}
                },
                "required": ["url"]
            }
        )

        tool_registry.register(
            name="python_eval",
            func=PythonToolExecutor.python_eval,
            description="Execute Python code safely",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "safe_mode": {"type": "boolean", "description": "Enable safety checks"}
                },
                "required": ["code"]
            },
            requires_approval=True
        )

        tool_registry.register(
            name="search",
            func=SearchToolExecutor.search,
            description="Search for information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results"}
                },
                "required": ["query"]
            }
        )

    return tool_registry


def get_agent_executor():
    """Get or initialize agent executor."""
    global agent_executor
    if agent_executor is None:
        registry = get_tool_registry()
        claude = get_claude_client()
        agent_executor = AgentExecutor(
            tool_registry=registry,
            claude_client=claude,
            model="claude-sonnet-4-6"
        )
    return agent_executor


def get_restrictions_manager():
    """Get or initialize restrictions manager."""
    global restrictions_manager
    if restrictions_manager is None:
        restrictions_manager = ToolRestrictionsManager()
    return restrictions_manager


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Check gateway health and status."""
    ollama = get_ollama_client()
    claude = get_claude_client()

    ollama_available = ollama.is_available()
    claude_available = False
    if claude:
        claude_available = claude.validate_api_key()

    # Get today's stats
    from datetime import timedelta
    from sqlalchemy import func
    from .database import AuditRequest

    cutoff = datetime.utcnow() - timedelta(days=1)
    requests_today = db.query(func.count(AuditRequest.id)).filter(
        AuditRequest.timestamp >= cutoff,
        AuditRequest.policy_decision == "approved",
    ).scalar() or 0

    cost_today = db.query(func.sum(AuditRequest.cost_usd)).filter(
        AuditRequest.timestamp >= cutoff,
        AuditRequest.policy_decision == "approved",
    ).scalar() or 0

    uptime = (datetime.utcnow() - app_start_time).total_seconds()

    return HealthResponse(
        status="healthy",
        gateway_version="1.0.0",
        models_available=["ollama"] if ollama_available else [],
        ollama_available=ollama_available,
        claude_api_key_valid=claude_available,
        uptime_seconds=int(uptime),
        requests_today=requests_today,
        cost_today_usd=round(cost_today or 0, 4),
    )


@app.post("/query", response_model=QueryResponse)
async def query_gateway(request: QueryRequest, db: Session = Depends(get_db)):
    """Main gateway endpoint: process a query through policy, routing, and execution."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"Request {request_id}: {request.user_id} -> {request.prompt[:50]}...")

    # Step 1: Policy evaluation
    policy_engine = PolicyEngine(db)
    policy_decision = policy_engine.evaluate(request)

    if not policy_decision.approved:
        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger = AuditLogger(db)
        audit_logger.log_policy_rejection(
            request.user_id,
            policy_decision.reason,
            request.prompt[:100],
        )
        logger.warning(f"Request {request_id} rejected: {policy_decision.reason}")

        raise HTTPException(
            status_code=403,
            detail={
                "error": "policy_violation",
                "reason": policy_decision.reason,
                "request_id": request_id,
            },
        )

    # Step 2: Model routing
    ollama = get_ollama_client()
    router = ModelRouter(ollama)
    model_name, endpoint = router.decide(request.prompt, request.model)
    logger.info(f"Request {request_id}: routed to {model_name}")

    # Step 3: Execution
    response_text = ""
    tokens_in = 0
    tokens_out = 0

    try:
        if endpoint == "local":
            response_text, tokens_out = ollama.query(request.prompt, model_name)
            tokens_in = CostCalculator.count_tokens(request.prompt)
        else:
            claude = get_claude_client()
            if not claude:
                raise Exception("Claude API key not configured")
            response_text, tokens_in, tokens_out = claude.query(
                request.prompt,
                model_name,
            )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Request {request_id} execution failed: {str(e)}")

        audit_logger = AuditLogger(db)
        audit_logger.log_request(
            request,
            None,
            "execution_failed",
            duration_ms,
            str(e),
        )

        raise HTTPException(
            status_code=503,
            detail={
                "error": "execution_failed",
                "reason": str(e),
                "request_id": request_id,
            },
        )

    # Step 4: Cost calculation
    cost_usd = CostCalculator.calculate_cost(model_name, tokens_in, tokens_out)

    # Step 5: Verify against final budget
    if cost_usd > request.budget_usd:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.warning(f"Request {request_id}: cost ${cost_usd} exceeds budget ${request.budget_usd}")

        audit_logger = AuditLogger(db)
        audit_logger.log_policy_rejection(
            request.user_id,
            "budget_exceeded_at_execution",
            f"Actual cost: ${cost_usd}",
        )

        raise HTTPException(
            status_code=403,
            detail={
                "error": "budget_exceeded",
                "reason": f"Actual cost ${cost_usd} exceeds budget ${request.budget_usd}",
                "request_id": request_id,
            },
        )

    # Step 6: Log success
    duration_ms = int((time.time() - start_time) * 1000)
    audit_logger = AuditLogger(db)

    response = QueryResponse(
        request_id=request_id,
        response=response_text,
        model_used=model_name,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        policy_decision="approved",
        duration_ms=duration_ms,
        timestamp=datetime.utcnow(),
    )

    audit_logger.log_request(request, response, "approved", duration_ms)

    logger.info(f"Request {request_id}: success ({duration_ms}ms, ${cost_usd})")

    return response


@app.get("/audit")
async def get_audit_log(
    user: str = Query(...),
    hours: int = Query(1, ge=1, le=24),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get audit log for a user."""
    audit_logger = AuditLogger(db)
    records = audit_logger.get_user_requests(user, hours)
    return {
        "user_id": user,
        "period_hours": hours,
        "records": records[:limit],
    }


@app.get("/audit/summary")
async def get_audit_summary(
    days: int = Query(1, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Get cost and usage summary."""
    audit_logger = AuditLogger(db)
    summary = audit_logger.get_daily_summary(days)
    return {
        "period_days": days,
        **summary.model_dump(),
    }


@app.get("/audit/violations")
async def get_violations(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get recent policy violations."""
    audit_logger = AuditLogger(db)
    violations = audit_logger.get_violations(hours)
    return {
        "period_hours": hours,
        "violations": violations,
    }


@app.get("/info")
async def get_info():
    """Get gateway info."""
    return {
        "name": "Policy-Aware AI Gateway",
        "version": "1.0.0",
        "mode": settings.gateway_mode,
        "models_whitelisted": settings.models_whitelist,
        "budget_per_request": settings.budget_per_request_usd,
        "budget_per_user_per_day": settings.budget_per_user_per_day_usd,
        "rate_limit_per_minute": settings.rate_limit_req_per_minute,
    }


# Phase 2: Agent Orchestration Endpoints

@app.post("/agent/run", response_model=AgentExecutionResponse)
async def run_agent(request: AgentRequestBody, db: Session = Depends(get_db)):
    """Execute an agent with tool calling capability."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"Agent {request_id}: {request.user_id} -> {request.goal[:50]}...")

    # Step 1: Validate user via policy engine
    policy_engine = PolicyEngine(db)
    query_request = QueryRequest(prompt=request.goal, user_id=request.user_id)
    policy_decision = policy_engine.evaluate(query_request)

    if not policy_decision.approved:
        logger.warning(f"Agent {request_id}: user rejected by policy: {policy_decision.reason}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "policy_violation",
                "reason": policy_decision.reason,
                "request_id": request_id,
            },
        )

    # Step 2: Check tool restrictions
    restrictions = get_restrictions_manager()
    # Verify agent can use tools (basic check - all tools available in Phase 2)

    # Step 3: Create agent request
    agent_request = AgentRequestModel(
        goal=request.goal,
        user_id=request.user_id,
        budget_usd=request.budget_usd,
        context=request.context,
        max_iterations=request.max_iterations,
        timeout_seconds=request.timeout_seconds,
    )

    # Step 4: Execute agent
    agent = get_agent_executor()
    try:
        result = await agent.run(agent_request)
    except Exception as e:
        logger.error(f"Agent {request_id}: execution failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "agent_execution_failed",
                "reason": str(e),
                "request_id": request_id,
            },
        )

    # Step 5: Log execution in audit trail
    audit_logger = AuditLogger(db)
    duration_ms = int((time.time() - start_time) * 1000)

    # Create audit record for agent execution
    from .database import AgentExecution
    agent_execution = AgentExecution(
        agent_id=result.agent_id,
        request_id=result.request_id,
        user_id=result.user_id,
        goal=result.goal,
        status=result.status,
        final_response=result.final_response,
        execution_trace=[step.model_dump() for step in result.execution_trace],
        tools_called=[tool.model_dump() for tool in result.tools_called],
        total_cost_usd=result.total_cost_usd,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
    )
    db.add(agent_execution)
    db.commit()

    logger.info(
        f"Agent {request_id}: {result.status} "
        f"({result.duration_ms}ms, ${result.total_cost_usd}, "
        f"{len(result.tools_called)} tools)"
    )

    # Return execution response
    from .models import ExecutionStepResponse, ToolCallResponse

    return AgentExecutionResponse(
        agent_id=result.agent_id,
        request_id=result.request_id,
        user_id=result.user_id,
        goal=result.goal,
        status=result.status,
        final_response=result.final_response,
        execution_trace=[
            ExecutionStepResponse(
                type=step.type,
                content=step.content,
                tool_call=ToolCallResponse(
                    name=step.tool_call.name,
                    args=step.tool_call.args,
                    timestamp=step.tool_call.timestamp,
                ) if step.tool_call else None,
                duration_ms=step.duration_ms,
            )
            for step in result.execution_trace
        ],
        tools_called=[
            ToolCallResponse(
                name=tool.name,
                args=tool.args,
                timestamp=tool.timestamp,
            )
            for tool in result.tools_called
        ],
        total_cost_usd=result.total_cost_usd,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
        timestamp=datetime.utcnow(),
    )


@app.get("/agent/executions", response_model=AgentExecutionHistoryResponse)
async def get_agent_executions(
    user: str = Query(...),
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get agent execution history for a user."""
    from .database import AgentExecution
    from sqlalchemy import desc

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    executions = db.query(AgentExecution).filter(
        AgentExecution.user_id == user,
        AgentExecution.timestamp >= cutoff,
    ).order_by(desc(AgentExecution.timestamp)).limit(limit).all()

    from .models import AgentExecutionHistoryItem

    return AgentExecutionHistoryResponse(
        user_id=user,
        total_executions=len(executions),
        total_cost_usd=sum(e.total_cost_usd for e in executions),
        executions=[
            AgentExecutionHistoryItem(
                agent_id=e.agent_id,
                request_id=e.request_id,
                goal=e.goal,
                status=e.status,
                total_cost_usd=e.total_cost_usd,
                duration_ms=e.duration_ms,
                timestamp=e.timestamp,
            )
            for e in executions
        ],
    )


@app.get("/agent/approvals", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    db: Session = Depends(get_db),
):
    """Get pending tool approval requests."""
    approval_engine = ToolApprovalEngine(db)
    pending = approval_engine.get_pending_approvals(limit=100)

    from .models import ToolApprovalRequestModel

    return PendingApprovalsResponse(
        total_pending=len(pending),
        approvals=[
            ToolApprovalRequestModel(
                approval_id=p.approval_id,
                user_id=p.user_id,
                tool_name=p.tool_name,
                args=p.args,
                created_at=p.created_at,
                status="pending",
            )
            for p in pending
        ],
    )


@app.post("/agent/approve/{approval_id}")
async def approve_tool_execution(
    approval_id: str,
    decision_request: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    """Approve a tool execution request."""
    approval_engine = ToolApprovalEngine(db)

    if decision_request.decision.lower() == "approve":
        success = approval_engine.approve(approval_id, "admin")
    else:
        success = approval_engine.reject(approval_id, "admin")

    if not success:
        raise HTTPException(status_code=404, detail="Approval not found")

    return {
        "approval_id": approval_id,
        "decision": decision_request.decision,
        "reason": decision_request.reason,
        "status": "processed",
    }


@app.get("/tools", response_model=ToolsListResponse)
async def list_tools():
    """List available tools."""
    registry = get_tool_registry()
    restrictions = get_restrictions_manager()

    tools = []
    for tool_def in registry.get_tool_definitions():
        restriction = restrictions.get_restriction(tool_def["name"])
        tools.append(
            ToolInfo(
                name=tool_def["name"],
                description=tool_def["description"],
                enabled=restriction.enabled if restriction else False,
                requires_approval=registry._tools[tool_def["name"]]["requires_approval"],
                input_schema=tool_def["input_schema"],
            )
        )

    return ToolsListResponse(
        total_tools=len(tools),
        tools=tools,
    )


# Phase 3: Real-Time Streaming Endpoints

@app.post("/agent/stream/session")
async def create_streaming_session(
    goal: str = Query(...),
    user_id: str = Query(...),
):
    """Create a new streaming session."""
    stream_manager = get_stream_manager()
    session_id = stream_manager.create_session(user_id, goal)

    return {
        "session_id": session_id,
        "user_id": user_id,
        "goal": goal,
        "status": "created",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.websocket("/agent/stream/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time agent execution streaming."""
    stream_manager = get_stream_manager()
    session = stream_manager.get_session(session_id)

    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    logger.info(f"WebSocket client connected to session {session_id}")

    try:
        async for event in stream_manager.stream_events(session_id):
            try:
                await websocket.send_json({
                    "type": event.type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "content": event.content,
                    "data": event.data,
                })
            except Exception as e:
                logger.error(f"Error sending event: {str(e)}")
                break
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


@app.get("/agent/stream/{session_id}/sse")
async def server_sent_events_stream(session_id: str):
    """Server-Sent Events endpoint for agent streaming (SSE fallback)."""
    stream_manager = get_stream_manager()
    session = stream_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        async for event in stream_manager.stream_events(session_id):
            yield event.to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/agent/stream/{session_id}/status")
async def stream_session_status(session_id: str):
    """Get status of a streaming session."""
    stream_manager = get_stream_manager()
    session = stream_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "completed": session.completed,
        "total_events": len(session.events),
        "total_cost_usd": session.total_cost_usd,
        "final_response": session.final_response,
        "created_at": session.created_at.isoformat(),
        "duration_seconds": (datetime.utcnow() - session.created_at).total_seconds(),
    }


@app.get("/agent/stream/{session_id}/history")
async def stream_session_history(session_id: str):
    """Get full history of a streaming session."""
    stream_manager = get_stream_manager()
    session = stream_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
