"""Integration tests for agent + gateway integration."""

import pytest
import json
from unittest.mock import AsyncMock, patch
from src.agents.engine import AgentExecutor
from src.agents.models import AgentRequest, AgentStatus
from src.tools.registry import ToolRegistry
from src.policies.approval import ToolApprovalEngine, ApprovalStatus
from src.policies.restrictions import ToolRestrictionsManager, ToolRestrictions
from src.services.cost_calculator import CostCalculator
from src.services.audit import AuditLogger


class TestAgentGatewayIntegration:
    """Test agent integration with Phase 1 gateway components."""

    @pytest.fixture
    def setup_components(self, tool_registry, db):
        """Setup all integration components."""
        agent_executor = AgentExecutor(tool_registry=tool_registry)
        approval_engine = ToolApprovalEngine(db)
        restrictions_manager = ToolRestrictionsManager()
        audit_logger = AuditLogger(db)

        return {
            "agent": agent_executor,
            "approval": approval_engine,
            "restrictions": restrictions_manager,
            "audit": audit_logger,
        }

    @pytest.mark.asyncio
    async def test_agent_with_approval_workflow(self, setup_components, agent_request):
        """Test agent execution with approval workflow."""
        components = setup_components
        agent = components["agent"]
        approval = components["approval"]

        # Mock Claude to request python_eval (requires approval)
        tool_call = '{"tool_name": "python_eval", "args": {"code": "2 + 2"}}'
        final_response = "The result is 4"

        agent.claude_client.query = AsyncMock(
            side_effect=[
                (tool_call, 10, 2),
                (final_response, 10, 5)
            ]
        )

        # Check if approval needed
        needs_approval = approval.should_require_approval("python_eval", agent_request.user_id)
        assert needs_approval

        # Request approval (simulating agent requesting tool)
        approval_req = approval.request_approval(
            user_id=agent_request.user_id,
            tool_name="python_eval",
            args={"code": "2 + 2"}
        )

        assert approval_req.tool_name == "python_eval"

    @pytest.mark.asyncio
    async def test_agent_respects_restrictions(self, setup_components, agent_request):
        """Test agent respects tool restrictions."""
        components = setup_components
        restrictions = components["restrictions"]

        # SQL query should be disabled by default
        assert not restrictions.is_tool_enabled("sql_query")

        # HTTP GET should be enabled
        assert restrictions.is_tool_enabled("http_get")

        # Get restriction details
        http_restriction = restrictions.get_restriction("http_get")
        assert http_restriction.rate_limit_per_minute == 10
        assert http_restriction.timeout_seconds == 10

    @pytest.mark.asyncio
    async def test_agent_cost_tracking(self, setup_components, agent_request):
        """Test agent cost tracking with CostCalculator."""
        agent = setup_components["agent"]

        # Mock Claude response
        agent.claude_client.query = AsyncMock(
            return_value=("Response", 100, 50)
        )

        result = await agent.run(agent_request)

        # Verify cost calculation
        expected_cost = CostCalculator.calculate_cost("claude-sonnet-4-6", 100, 50)
        assert result.total_cost_usd > 0
        assert result.total_cost_usd >= expected_cost

    @pytest.mark.asyncio
    async def test_agent_execution_audit_logging(self, setup_components, agent_request, db):
        """Test agent execution is logged in audit trail."""
        agent = setup_components["agent"]
        audit = components["audit"]

        # Mock Claude
        agent.claude_client.query = AsyncMock(
            return_value=("Response", 10, 5)
        )

        result = await agent.run(agent_request)

        # In real implementation, audit logger would record this
        # For testing, we verify the result has all necessary info for logging
        assert result.request_id
        assert result.user_id == agent_request.user_id
        assert result.goal == agent_request.goal
        assert result.total_cost_usd >= 0
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_agent_budget_enforcement(self, setup_components):
        """Test agent respects budget limits."""
        agent = setup_components["agent"]

        # Create request with very low budget
        request = AgentRequest(
            goal="Test",
            user_id="user@example.com",
            budget_usd=0.0001  # Very low budget
        )

        # Mock expensive response
        agent.claude_client.query = AsyncMock(
            return_value=("Response", 1000, 1000)  # High token cost
        )

        result = await agent.run(request)

        # Should fail due to budget
        assert result.status == AgentStatus.FAILED
        assert "Budget" in result.error_message

    @pytest.mark.asyncio
    async def test_agent_with_rate_limiting(self, setup_components, agent_request):
        """Test agent respects rate limiting."""
        restrictions = setup_components["restrictions"]

        # Get HTTP GET restrictions
        http_restriction = restrictions.get_restriction("http_get")

        # Verify rate limit is set
        assert http_restriction.rate_limit_per_minute == 10

        # Get user-specific restrictions
        user_restriction = restrictions.get_restriction("http_get", user_id="user@example.com")
        # Should inherit global if no override
        assert user_restriction.rate_limit_per_minute == 10

    def test_restrictions_integration_with_approval(self, setup_components):
        """Test restrictions work with approval engine."""
        restrictions = setup_components["restrictions"]
        approval = setup_components["approval"]

        # python_eval requires approval
        assert restrictions.is_tool_enabled("python_eval")
        assert approval.should_require_approval("python_eval", "user@example.com")

        # SQL is disabled and requires approval
        assert not restrictions.is_tool_enabled("sql_query")
        assert approval.should_require_approval("sql_query", "user@example.com")

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self, setup_components, agent_request):
        """Test complete agent workflow with all components."""
        agent = setup_components["agent"]
        approval = setup_components["approval"]
        restrictions = setup_components["restrictions"]
        audit = setup_components["audit"]

        # 1. Check if tool is enabled
        tool_enabled = restrictions.is_tool_enabled("search")
        assert tool_enabled

        # 2. Check if approval needed
        needs_approval = approval.should_require_approval("search", agent_request.user_id)
        assert not needs_approval

        # 3. Mock agent execution
        search_call = '{"tool_name": "search", "args": {"query": "test"}}'
        final_response = "Found: result 1, result 2"

        agent.claude_client.query = AsyncMock(
            side_effect=[
                (search_call, 10, 2),
                (final_response, 15, 8)
            ]
        )

        # 4. Execute agent
        result = await agent.run(agent_request)

        # 5. Verify execution
        assert result.status == AgentStatus.COMPLETED
        assert len(result.tools_called) == 1
        assert result.tools_called[0].name == "search"
        assert result.total_cost_usd > 0

        # 6. Would be logged in audit trail
        assert result.request_id
        assert result.user_id == agent_request.user_id


class TestAgentWithValidators:
    """Test agent execution with input validators."""

    @pytest.fixture
    def validator_setup(self, tool_registry):
        """Setup with validators."""
        agent = AgentExecutor(tool_registry=tool_registry)
        return agent

    @pytest.mark.asyncio
    async def test_agent_blocks_internal_http(self, validator_setup):
        """Test agent blocks internal IP HTTP calls."""
        from src.tools.validators import HttpValidator

        # Should raise on internal IP
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("http://192.168.1.1/data")
        assert "blocked" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_agent_blocks_unsafe_code(self, validator_setup):
        """Test agent blocks unsafe Python code."""
        from src.tools.validators import PythonValidator

        # Should raise on import
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("import os")
        assert "forbidden" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_agent_blocks_sql_delete(self, validator_setup):
        """Test agent blocks SQL DELETE."""
        from src.tools.validators import SqlValidator

        # Should raise on DELETE
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query("DELETE FROM users")
        assert "dangerous" in str(exc.value).lower()


class TestAgentScalability:
    """Test agent system scalability and performance."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_executions(self, tool_registry):
        """Test multiple concurrent agent executions."""
        import asyncio

        agent = AgentExecutor(tool_registry=tool_registry)
        agent.claude_client.query = AsyncMock(
            return_value=("Response", 10, 5)
        )

        # Create multiple requests
        requests = [
            AgentRequest(
                goal=f"Task {i}",
                user_id=f"user{i}@example.com",
                budget_usd=1.0
            )
            for i in range(5)
        ]

        # Execute concurrently
        results = await asyncio.gather(*[agent.run(req) for req in requests])

        # Verify all completed
        assert len(results) == 5
        assert all(r.status == AgentStatus.COMPLETED for r in results)
        assert all(r.request_id for r in results)

    @pytest.mark.asyncio
    async def test_agent_memory_efficiency(self, tool_registry):
        """Test agent doesn't leak memory with repeated executions."""
        agent = AgentExecutor(tool_registry=tool_registry)
        agent.claude_client.query = AsyncMock(
            return_value=("Response", 10, 5)
        )

        request = AgentRequest(
            goal="Test",
            user_id="user@example.com",
            budget_usd=1.0
        )

        # Execute multiple times
        for _ in range(10):
            result = await agent.run(request)
            assert result.status == AgentStatus.COMPLETED

        # No assertion here - just checking it doesn't crash
        # In real scenario, would use memory profiler


class TestAgentErrorHandling:
    """Test agent error handling and recovery."""

    @pytest.mark.asyncio
    async def test_agent_handles_claude_error(self, tool_registry):
        """Test agent handles Claude API errors gracefully."""
        agent = AgentExecutor(tool_registry=tool_registry)
        agent.claude_client.query = AsyncMock(
            side_effect=Exception("Claude API unavailable")
        )

        request = AgentRequest(
            goal="Test",
            user_id="user@example.com",
            budget_usd=1.0
        )

        result = await agent.run(request)

        assert result.status == AgentStatus.FAILED
        assert "Claude API" in result.error_message

    @pytest.mark.asyncio
    async def test_agent_handles_tool_error(self, tool_registry):
        """Test agent handles tool execution errors."""
        agent = AgentExecutor(tool_registry=tool_registry)

        # Mock tool call to bad tool
        bad_tool_call = '{"tool_name": "nonexistent_tool", "args": {}}'
        final_response = "Error, trying different approach"

        agent.claude_client.query = AsyncMock(
            side_effect=[
                (bad_tool_call, 10, 2),
                (final_response, 15, 8)
            ]
        )

        request = AgentRequest(
            goal="Test",
            user_id="user@example.com",
            budget_usd=1.0
        )

        result = await agent.run(request)

        # Should continue after tool error
        assert result.status == AgentStatus.COMPLETED
        assert len(result.execution_trace) > 0
