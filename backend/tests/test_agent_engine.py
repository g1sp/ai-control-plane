"""Tests for agent execution engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.engine import AgentExecutor
from src.agents.models import AgentRequest, AgentStatus, StepType
from src.tools.registry import ToolRegistry
from src.integrations.claude import ClaudeClient


class TestAgentExecutor:
    """Test agent execution engine."""

    @pytest.fixture
    def agent_executor(self, tool_registry):
        """Create agent executor with mocked Claude client."""
        mock_claude = AsyncMock(spec=ClaudeClient)
        return AgentExecutor(
            tool_registry=tool_registry,
            claude_client=mock_claude,
            model="claude-sonnet-4-6",
            max_iterations=5
        )

    @pytest.mark.asyncio
    async def test_agent_simple_response(self, agent_executor, agent_request):
        """Test agent with simple response (no tool use)."""
        agent_executor.claude_client.query = AsyncMock(
            return_value=("The answer is 42", 10, 5)
        )

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.COMPLETED
        assert result.user_id == "test@example.com"
        assert result.goal == "Test goal"
        assert result.total_cost_usd > 0
        assert result.duration_ms > 0
        assert len(result.execution_trace) > 0

    @pytest.mark.asyncio
    async def test_agent_with_tool_call(self, agent_executor, agent_request):
        """Test agent making a tool call."""
        # First call: Claude wants to search
        search_response = '{"tool_name": "search", "args": {"query": "test query", "limit": 5}}'
        # Second call: Claude gives final answer
        final_response = "Based on search results: ..."

        agent_executor.claude_client.query = AsyncMock(
            side_effect=[
                (search_response, 15, 3),  # First iteration
                (final_response, 20, 10)   # Second iteration
            ]
        )

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.COMPLETED
        assert len(result.tools_called) == 1
        assert result.tools_called[0].name == "search"
        assert any(step.type == StepType.TOOL_CALL for step in result.execution_trace)

    @pytest.mark.asyncio
    async def test_agent_budget_exceeded(self, agent_executor, agent_request):
        """Test agent stops when budget exceeded."""
        agent_request.budget_usd = 0.001  # Very low budget

        agent_executor.claude_client.query = AsyncMock(
            return_value=("Response", 1000, 1000)  # High token cost
        )

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.FAILED
        assert "Budget exceeded" in result.error_message

    @pytest.mark.asyncio
    async def test_agent_timeout(self, agent_executor, agent_request):
        """Test agent timeout."""
        agent_request.timeout_seconds = 0.001  # Very short timeout

        async def slow_query(*args, **kwargs):
            import asyncio
            await asyncio.sleep(1)
            return ("Response", 10, 5)

        agent_executor.claude_client.query = slow_query

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.FAILED
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_agent_max_iterations(self, agent_executor, agent_request):
        """Test agent max iterations limit."""
        agent_request.max_iterations = 2

        # Keep returning tool calls (never finishes)
        tool_call = '{"tool_name": "search", "args": {"query": "test"}}'
        agent_executor.claude_client.query = AsyncMock(return_value=(tool_call, 10, 2))

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_agent_tool_error_handling(self, agent_executor, agent_request):
        """Test agent handles tool errors gracefully."""
        # Claude calls non-existent tool
        bad_tool_call = '{"tool_name": "nonexistent", "args": {}}'
        final_response = "Error occurred, trying another approach..."

        agent_executor.claude_client.query = AsyncMock(
            side_effect=[
                (bad_tool_call, 10, 2),
                (final_response, 15, 8)
            ]
        )

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.COMPLETED
        assert any(step.type == StepType.ERROR for step in result.execution_trace)

    @pytest.mark.asyncio
    async def test_agent_execution_trace(self, agent_executor, agent_request):
        """Test agent records execution trace."""
        search_response = '{"tool_name": "search", "args": {"query": "test"}}'
        final_response = "Here are the results..."

        agent_executor.claude_client.query = AsyncMock(
            side_effect=[
                (search_response, 10, 2),
                (final_response, 15, 8)
            ]
        )

        result = await agent_executor.run(agent_request)

        # Should have thinking, tool call, tool result, thinking, done steps
        assert len(result.execution_trace) > 0
        step_types = [step.type for step in result.execution_trace]
        assert StepType.THINKING in step_types or StepType.TOOL_CALL in step_types

    @pytest.mark.asyncio
    async def test_agent_cost_tracking(self, agent_executor, agent_request):
        """Test agent tracks cost correctly."""
        agent_executor.claude_client.query = AsyncMock(
            return_value=("Response", 100, 50)
        )

        result = await agent_executor.run(agent_request)

        # Cost should be calculated based on token counts
        assert result.total_cost_usd > 0

    @pytest.mark.asyncio
    async def test_agent_multiple_tools(self, agent_executor, agent_request):
        """Test agent calling multiple tools."""
        call1 = '{"tool_name": "search", "args": {"query": "weather"}}'
        call2 = '{"tool_name": "search", "args": {"query": "forecast"}}'
        final = "Based on multiple searches..."

        agent_executor.claude_client.query = AsyncMock(
            side_effect=[
                (call1, 10, 2),
                (call2, 10, 2),
                (final, 15, 8)
            ]
        )

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.COMPLETED
        assert len(result.tools_called) == 2

    def test_build_system_prompt(self, agent_executor):
        """Test system prompt generation."""
        tools = [
            {
                "name": "test",
                "description": "Test tool",
                "input_schema": {"type": "object"}
            }
        ]

        prompt = agent_executor._build_system_prompt(tools)

        assert "helpful AI assistant" in prompt
        assert "tool" in prompt.lower()
        assert "test" in prompt

    def test_is_final_response(self, agent_executor):
        """Test detecting final responses."""
        # Valid JSON = tool call (not final)
        assert not agent_executor._is_final_response('{"tool_name": "search"}')

        # Plain text = final response
        assert agent_executor._is_final_response("This is the final answer")

        # Invalid JSON = final response
        assert agent_executor._is_final_response("Not {valid json")

    def test_parse_tool_calls(self, agent_executor):
        """Test parsing tool calls from response."""
        # Valid tool call
        calls = agent_executor._parse_tool_calls('{"tool_name": "search", "args": {"q": "test"}}')
        assert len(calls) == 1
        assert calls[0].name == "search"
        assert calls[0].args == {"q": "test"}

        # No tool call
        calls = agent_executor._parse_tool_calls("Plain text response")
        assert len(calls) == 0

    @pytest.mark.asyncio
    async def test_agent_result_structure(self, agent_executor, agent_request):
        """Test agent result has all required fields."""
        agent_executor.claude_client.query = AsyncMock(
            return_value=("Response", 10, 5)
        )

        result = await agent_executor.run(agent_request)

        assert result.agent_id.startswith("agent_")
        assert result.request_id.startswith("req_")
        assert result.user_id
        assert result.goal
        assert result.status
        assert result.final_response
        assert result.execution_trace is not None
        assert result.tools_called is not None
        assert result.total_cost_usd >= 0
        assert result.duration_ms > 0
        assert result.timestamp

    @pytest.mark.asyncio
    async def test_agent_with_context(self, agent_executor, agent_request):
        """Test agent with additional context."""
        agent_request.context = {"user_name": "Alice", "session": "123"}

        agent_executor.claude_client.query = AsyncMock(
            return_value=("Response", 10, 5)
        )

        result = await agent_executor.run(agent_request)

        assert result.status == AgentStatus.COMPLETED
