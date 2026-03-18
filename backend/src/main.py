"""FastAPI application for Policy-Aware AI Gateway."""

import time
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .database import init_db, get_db
from .models import QueryRequest, QueryResponse, ErrorResponse, HealthResponse
from .services.policy import PolicyEngine
from .services.router import ModelRouter
from .services.audit import AuditLogger
from .services.cost_calculator import CostCalculator
from .integrations.ollama import OllamaClient
from .integrations.claude import ClaudeClient
from .utils.logger import logger

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
