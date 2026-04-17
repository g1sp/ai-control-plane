from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime
from enum import Enum


class StepType(str, Enum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"


class AgentStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ToolCall(BaseModel):
    name: str = Field(..., description="Tool name")
    args: Dict[str, Any] = Field(..., description="Tool arguments")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentStep(BaseModel):
    type: StepType = Field(..., description="Step type")
    content: str = Field(..., description="Step content/output")
    tool_call: Optional[ToolCall] = Field(None, description="Tool call details if applicable")
    duration_ms: int = Field(default=0, description="Step execution time")


class AgentRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=5000, description="Agent goal/task")
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID")
    budget_usd: float = Field(default=1.0, ge=0.001, description="Budget limit in USD")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_iterations: int = Field(default=10, ge=1, le=50, description="Max reasoning iterations")
    timeout_seconds: int = Field(default=60, ge=5, le=600, description="Timeout in seconds")


class AgentResult(BaseModel):
    agent_id: str = Field(..., description="Unique agent execution ID")
    request_id: str = Field(..., description="Request ID for tracking")
    user_id: str = Field(..., description="User who ran the agent")
    goal: str = Field(..., description="Original goal")
    status: AgentStatus = Field(..., description="Execution status")
    final_response: str = Field(..., description="Agent's final response")
    execution_trace: List[AgentStep] = Field(default_factory=list, description="Step-by-step trace")
    tools_called: List[ToolCall] = Field(default_factory=list, description="All tools called")
    total_cost_usd: float = Field(default=0.0, description="Total execution cost")
    duration_ms: int = Field(default=0, description="Total execution time")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_abc123",
                "request_id": "req_xyz789",
                "user_id": "alice@company.com",
                "goal": "Get current weather for New York",
                "status": "completed",
                "final_response": "The current weather in New York is...",
                "execution_trace": [],
                "tools_called": [],
                "total_cost_usd": 0.02,
                "duration_ms": 1250,
                "timestamp": "2026-04-16T12:30:45Z"
            }
        }
