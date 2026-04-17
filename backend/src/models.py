"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PolicyDecisionEnum(str, Enum):
    """Policy decision outcomes."""
    APPROVED = "approved"
    REJECTED = "rejected"
    RATE_LIMITED = "rate_limited"
    BUDGET_EXCEEDED = "budget_exceeded"
    USER_NOT_WHITELISTED = "user_not_whitelisted"
    MODEL_NOT_WHITELISTED = "model_not_whitelisted"
    INJECTION_DETECTED = "injection_detected"


class QueryRequest(BaseModel):
    """Incoming query request."""
    prompt: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="auto", description="Model: auto, ollama, claude-sonnet-4-6, etc")
    user_id: str = Field(..., min_length=1, max_length=100)
    budget_usd: float = Field(default=0.1, ge=0.001, description="Per-request budget in USD")
    timeout_seconds: int = Field(default=30, ge=5, le=120)


class PolicyDecision(BaseModel):
    """Policy evaluation result."""
    approved: bool
    reason: str
    rate_limited_until: Optional[datetime] = None


class QueryResponse(BaseModel):
    """Successful query response."""
    request_id: str
    response: str
    model_used: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    policy_decision: str  # "approved" or reason
    duration_ms: int
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    reason: str
    details: Optional[str] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    gateway_version: str
    models_available: list[str]
    ollama_available: bool
    claude_api_key_valid: bool
    uptime_seconds: int
    requests_today: int
    cost_today_usd: float


class AuditRecord(BaseModel):
    """Audit log entry."""
    id: int
    timestamp: datetime
    user_id: str
    prompt_summary: str  # First 100 chars
    model_used: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    policy_decision: str
    duration_ms: int
    error_message: Optional[str] = None


class SummaryStats(BaseModel):
    """Cost and usage summary."""
    total_requests: int
    total_cost_usd: float
    total_tokens: int
    requests_by_model: dict[str, int]
    cost_by_model: dict[str, float]
    top_users: list[dict]
    violations: int
    average_cost_per_request: float


# Phase 2: Agent Models (new)

class AgentRequestBody(BaseModel):
    """Request body for /agent/run endpoint."""
    goal: str = Field(..., min_length=1, max_length=5000, description="Agent goal/task")
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID")
    budget_usd: float = Field(default=1.0, ge=0.001, description="Budget limit in USD")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_iterations: int = Field(default=10, ge=1, le=50, description="Max reasoning iterations")
    timeout_seconds: int = Field(default=60, ge=5, le=600, description="Timeout in seconds")


class ToolCallResponse(BaseModel):
    """Tool call in execution trace."""
    name: str
    args: Dict[str, Any]
    timestamp: datetime


class ExecutionStepResponse(BaseModel):
    """Step in execution trace."""
    type: str  # thinking, tool_call, tool_result, done, error
    content: str
    tool_call: Optional[ToolCallResponse] = None
    duration_ms: int = 0


class AgentExecutionResponse(BaseModel):
    """Response for agent execution."""
    agent_id: str
    request_id: str
    user_id: str
    goal: str
    status: str  # completed, failed, timeout
    final_response: str
    execution_trace: List[ExecutionStepResponse]
    tools_called: List[ToolCallResponse]
    total_cost_usd: float
    duration_ms: int
    error_message: Optional[str] = None
    timestamp: datetime


class AgentExecutionHistoryItem(BaseModel):
    """Single item in execution history."""
    agent_id: str
    request_id: str
    goal: str
    status: str
    total_cost_usd: float
    duration_ms: int
    timestamp: datetime


class AgentExecutionHistoryResponse(BaseModel):
    """Response for agent execution history."""
    user_id: str
    total_executions: int
    total_cost_usd: float
    executions: List[AgentExecutionHistoryItem]


class ToolApprovalRequestModel(BaseModel):
    """Tool approval request item."""
    approval_id: str
    user_id: str
    tool_name: str
    args: Optional[Dict[str, Any]] = None
    created_at: datetime
    status: str  # pending, approved, rejected


class PendingApprovalsResponse(BaseModel):
    """Response for pending approvals list."""
    total_pending: int
    approvals: List[ToolApprovalRequestModel]


class ApprovalDecisionRequest(BaseModel):
    """Request to approve/reject a tool execution."""
    decision: str = Field(..., description="approve or reject")
    reason: Optional[str] = Field(None, description="Optional reason for decision")


class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    description: str
    enabled: bool
    requires_approval: bool
    input_schema: Dict[str, Any]


class ToolsListResponse(BaseModel):
    """Response for tools list."""
    total_tools: int
    tools: List[ToolInfo]
