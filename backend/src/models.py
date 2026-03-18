"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
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
