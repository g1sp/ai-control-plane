"""Core agent execution engine with reasoning loop."""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import AgentRequest, AgentResult, AgentStep, AgentStatus, StepType, ToolCall
from ..tools.registry import ToolRegistry
from ..integrations.claude import ClaudeClient
from ..services.cost_calculator import CostCalculator


class AgentExecutor:
    """Execute multi-step agent reasoning with tool calling."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        claude_client: Optional[ClaudeClient] = None,
        model: str = "claude-sonnet-4-6",
        max_iterations: int = 10,
    ):
        self.tool_registry = tool_registry
        self.claude_client = claude_client or ClaudeClient()
        self.model = model
        self.max_iterations = max_iterations

    async def run(self, request: AgentRequest) -> AgentResult:
        """Execute agent reasoning loop.

        Args:
            request: AgentRequest with goal and parameters

        Returns:
            AgentResult with execution trace and final response
        """
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        request_id = f"req_{uuid.uuid4().hex[:12]}"

        execution_trace: List[AgentStep] = []
        tools_called: List[ToolCall] = []
        total_cost_usd = 0.0
        start_time = time.time()

        try:
            # Build initial prompt
            tool_definitions = self.tool_registry.get_tool_definitions()
            system_prompt = self._build_system_prompt(tool_definitions)
            user_message = f"Goal: {request.goal}\n\nContext: {json.dumps(request.context or {})}"

            messages = [{"role": "user", "content": user_message}]

            iteration = 0
            while iteration < self.max_iterations:
                iteration += 1

                # Check timeout
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms > request.timeout_seconds * 1000:
                    raise Exception(f"Execution timeout ({request.timeout_seconds}s exceeded)")

                # Call Claude with tool definitions
                try:
                    response, tokens_in, tokens_out = await self.claude_client.query(
                        prompt=json.dumps(messages),
                        model=self.model,
                    )

                    # Calculate cost
                    cost = CostCalculator.calculate_cost(self.model, tokens_in, tokens_out)
                    total_cost_usd += cost

                    if total_cost_usd > request.budget_usd:
                        raise Exception(f"Budget exceeded: ${total_cost_usd:.4f} > ${request.budget_usd:.4f}")

                except Exception as e:
                    raise Exception(f"Claude API error: {str(e)}")

                # Check if Claude finished (no tool calls)
                if self._is_final_response(response):
                    # Add final thinking step
                    execution_trace.append(
                        AgentStep(
                            type=StepType.THINKING,
                            content=response,
                        )
                    )
                    # Add done step
                    execution_trace.append(
                        AgentStep(
                            type=StepType.DONE,
                            content="Agent reasoning complete",
                        )
                    )
                    break

                # Parse tool calls from response
                tool_calls_list = self._parse_tool_calls(response)
                if not tool_calls_list:
                    execution_trace.append(
                        AgentStep(
                            type=StepType.THINKING,
                            content=response,
                        )
                    )
                    continue

                # Execute tools
                tool_results = []
                for tool_call in tool_calls_list:
                    tool_start = time.time()
                    try:
                        # Execute tool
                        result = await self.tool_registry.call(tool_call.name, **tool_call.args)

                        # Log tool call
                        tools_called.append(tool_call)
                        tool_duration_ms = int((time.time() - tool_start) * 1000)

                        execution_trace.append(
                            AgentStep(
                                type=StepType.TOOL_CALL,
                                content=f"Called {tool_call.name} with args: {tool_call.args}",
                                tool_call=tool_call,
                                duration_ms=tool_duration_ms,
                            )
                        )

                        execution_trace.append(
                            AgentStep(
                                type=StepType.TOOL_RESULT,
                                content=result,
                            )
                        )

                        tool_results.append(
                            {
                                "tool": tool_call.name,
                                "result": result,
                            }
                        )

                    except Exception as e:
                        execution_trace.append(
                            AgentStep(
                                type=StepType.ERROR,
                                content=f"Tool error: {str(e)}",
                            )
                        )

                # Add tool results to messages for next iteration
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Tool results: {json.dumps(tool_results)}",
                    }
                )

            # Determine final status
            if iteration >= self.max_iterations:
                status = AgentStatus.TIMEOUT
                final_response = "Max iterations reached"
            else:
                status = AgentStatus.COMPLETED
                final_response = response

            duration_ms = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_id=agent_id,
                request_id=request_id,
                user_id=request.user_id,
                goal=request.goal,
                status=status,
                final_response=final_response,
                execution_trace=execution_trace,
                tools_called=tools_called,
                total_cost_usd=total_cost_usd,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                agent_id=agent_id,
                request_id=request_id,
                user_id=request.user_id,
                goal=request.goal,
                status=AgentStatus.FAILED,
                final_response="",
                execution_trace=execution_trace,
                tools_called=tools_called,
                total_cost_usd=total_cost_usd,
                duration_ms=duration_ms,
                error_message=str(e),
            )

    def _build_system_prompt(self, tool_definitions: List[Dict[str, Any]]) -> str:
        """Build system prompt for Claude."""
        return f"""You are a helpful AI assistant with access to tools.

When you want to use a tool, respond with JSON in this format:
{{"tool_name": "tool_name", "args": {{"arg1": "value1"}}}}

Available tools:
{json.dumps(tool_definitions, indent=2)}

Use tools to help accomplish the goal. When done, respond naturally without tool calls."""

    def _is_final_response(self, response: str) -> bool:
        """Check if response is final (no tool calls)."""
        try:
            json.loads(response)
            return False  # Valid JSON = tool call
        except:
            return True  # Not JSON = final response

    def _parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from Claude response."""
        tool_calls = []
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "tool_name" in data:
                tool_calls.append(
                    ToolCall(
                        name=data["tool_name"],
                        args=data.get("args", {}),
                    )
                )
        except (json.JSONDecodeError, TypeError):
            pass
        return tool_calls
