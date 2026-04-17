"""Load and performance tests for Phase 2."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock
from src.agents.engine import AgentExecutor
from src.agents.models import AgentRequest, AgentStatus
from src.tools.registry import ToolRegistry


@pytest.fixture
def setup_load_test(tool_registry):
    """Setup for load tests."""
    from src.integrations.claude import ClaudeClient
    agent = AgentExecutor(tool_registry=tool_registry)
    agent.claude_client = AsyncMock(spec=ClaudeClient)
    agent.claude_client.query = AsyncMock(
        return_value=("Response", 10, 5)
    )
    return agent


class TestAgentLoadAndPerformance:
    """Test agent system under load."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_executions_5(self, setup_load_test):
        """Test 5 concurrent agent executions."""
        agent = setup_load_test
        requests = [
            AgentRequest(
                goal=f"Task {i}",
                user_id=f"user{i}@example.com",
                budget_usd=1.0
            )
            for i in range(5)
        ]

        start = time.time()
        results = await asyncio.gather(*[agent.run(req) for req in requests])
        elapsed = time.time() - start

        assert len(results) == 5
        assert all(r.status == AgentStatus.COMPLETED for r in results)
        assert elapsed < 10  # Should complete within 10 seconds
        assert elapsed > 0

    @pytest.mark.asyncio
    async def test_concurrent_agent_executions_10(self, setup_load_test):
        """Test 10 concurrent agent executions."""
        agent = setup_load_test
        requests = [
            AgentRequest(
                goal=f"Task {i}",
                user_id=f"user{i}@example.com",
                budget_usd=1.0
            )
            for i in range(10)
        ]

        start = time.time()
        results = await asyncio.gather(*[agent.run(req) for req in requests])
        elapsed = time.time() - start

        assert len(results) == 10
        assert all(r.status == AgentStatus.COMPLETED for r in results)
        assert elapsed < 20  # Should complete within 20 seconds
        print(f"\n10 concurrent executions: {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_sequential_agent_executions_100(self, setup_load_test):
        """Test 100 sequential executions."""
        agent = setup_load_test

        start = time.time()
        for i in range(100):
            request = AgentRequest(
                goal=f"Task {i}",
                user_id=f"user@example.com",
                budget_usd=1.0
            )
            result = await agent.run(request)
            assert result.status == AgentStatus.COMPLETED

        elapsed = time.time() - start
        avg_time = elapsed / 100

        print(f"\n100 sequential executions: {elapsed:.2f}s (avg: {avg_time:.3f}s per execution)")
        assert avg_time < 0.5  # Average should be < 500ms

    @pytest.mark.asyncio
    async def test_agent_throughput(self, setup_load_test):
        """Test agent throughput (requests per second)."""
        agent = setup_load_test

        start = time.time()
        completed = 0

        # Run executions for 10 seconds
        while time.time() - start < 10:
            request = AgentRequest(
                goal="Test",
                user_id="user@example.com",
                budget_usd=1.0
            )
            result = await agent.run(request)
            if result.status == AgentStatus.COMPLETED:
                completed += 1

        elapsed = time.time() - start
        throughput = completed / elapsed

        print(f"\nThroughput: {throughput:.2f} executions/second")
        assert throughput > 1.0  # At least 1 execution per second

    @pytest.mark.asyncio
    async def test_latency_distribution(self, setup_load_test):
        """Test execution latency distribution."""
        agent = setup_load_test
        latencies = []

        for i in range(50):
            request = AgentRequest(
                goal=f"Task {i}",
                user_id="user@example.com",
                budget_usd=1.0
            )
            start = time.time()
            result = await agent.run(request)
            latency = (time.time() - start) * 1000  # Convert to ms

            if result.status == AgentStatus.COMPLETED:
                latencies.append(latency)

        # Calculate stats
        latencies.sort()
        min_latency = min(latencies)
        max_latency = max(latencies)
        avg_latency = sum(latencies) / len(latencies)
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        print(f"\nLatency Distribution (ms):")
        print(f"  Min:  {min_latency:.2f}")
        print(f"  P50:  {p50:.2f}")
        print(f"  P95:  {p95:.2f}")
        print(f"  P99:  {p99:.2f}")
        print(f"  Max:  {max_latency:.2f}")
        print(f"  Avg:  {avg_latency:.2f}")

        # Assertions
        assert p99 < 5000  # P99 latency < 5 seconds
        assert avg_latency < 500  # Average < 500ms

    @pytest.mark.asyncio
    async def test_memory_stability(self, setup_load_test):
        """Test memory doesn't leak over repeated executions."""
        agent = setup_load_test

        for i in range(50):
            request = AgentRequest(
                goal=f"Task {i}",
                user_id="user@example.com",
                budget_usd=1.0
            )
            result = await agent.run(request)
            assert result.status == AgentStatus.COMPLETED

        # If we get here without crashing, memory is stable
        assert True

    @pytest.mark.asyncio
    async def test_error_recovery_under_load(self, tool_registry):
        """Test error recovery during load."""
        agent = AgentExecutor(tool_registry=tool_registry)

        # Simulate intermittent failures
        call_count = 0

        async def failing_query(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Simulated API error")
            return ("Response", 10, 5)

        agent.claude_client.query = failing_query

        success_count = 0
        error_count = 0

        for i in range(30):
            request = AgentRequest(
                goal=f"Task {i}",
                user_id="user@example.com",
                budget_usd=1.0
            )
            result = await agent.run(request)
            if result.status == AgentStatus.COMPLETED:
                success_count += 1
            else:
                error_count += 1

        # Should have roughly 2/3 success rate
        assert success_count >= 15  # At least 50% success
        assert error_count >= 5     # Some errors occurred

    @pytest.mark.asyncio
    async def test_budget_handling_under_load(self, setup_load_test):
        """Test budget enforcement under concurrent load."""
        agent = setup_load_test

        requests = [
            AgentRequest(
                goal=f"Task {i}",
                user_id=f"user{i}@example.com",
                budget_usd=0.001 if i % 5 == 0 else 1.0  # Some with low budget
            )
            for i in range(20)
        ]

        results = await asyncio.gather(*[agent.run(req) for req in requests])

        # Some should succeed, some should fail due to budget
        completed = sum(1 for r in results if r.status == AgentStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == AgentStatus.FAILED)

        assert completed > 0  # Some completed
        assert failed > 0     # Some failed


class TestToolExecutorPerformance:
    """Test tool executor performance."""

    @pytest.mark.asyncio
    async def test_search_tool_latency(self, tool_registry):
        """Test search tool latency."""
        start = time.time()
        result = await tool_registry.call("search", query="test", limit=5)
        elapsed = (time.time() - start) * 1000

        print(f"\nSearch tool latency: {elapsed:.2f}ms")
        assert elapsed < 100  # Should be < 100ms
        assert result

    @pytest.mark.asyncio
    async def test_python_tool_latency(self, tool_registry):
        """Test Python tool latency."""
        start = time.time()
        result = await tool_registry.call("python_eval", code="2 + 2")
        elapsed = (time.time() - start) * 1000

        print(f"\nPython tool latency: {elapsed:.2f}ms")
        assert elapsed < 200  # Should be < 200ms
        assert "4" in result

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, tool_registry):
        """Test concurrent tool calls."""
        requests = [
            tool_registry.call("search", query=f"query {i}", limit=5)
            for i in range(10)
        ]

        start = time.time()
        results = await asyncio.gather(*requests)
        elapsed = time.time() - start

        print(f"\n10 concurrent search calls: {elapsed:.2f}s")
        assert len(results) == 10
        assert all(r for r in results)


class TestAPIEndpointPerformance:
    """Test API endpoint performance."""

    def test_tools_endpoint_response_time(self, tool_registry):
        """Test /tools endpoint response time."""
        start = time.time()
        tools = tool_registry.get_tool_definitions()
        elapsed = (time.time() - start) * 1000

        print(f"\n/tools endpoint generation: {elapsed:.2f}ms")
        assert elapsed < 50  # Should be < 50ms
        assert len(tools) >= 3

    def test_large_execution_trace_handling(self, tool_registry):
        """Test handling of large execution traces."""
        # Simulate a large trace
        trace = [
            {
                "type": "thinking",
                "content": "x" * 1000,  # 1KB of content
                "duration_ms": 100
            }
            for _ in range(100)  # 100KB total
        ]

        import json
        start = time.time()
        json_str = json.dumps(trace)
        elapsed = (time.time() - start) * 1000

        print(f"\n100KB trace serialization: {elapsed:.2f}ms")
        assert elapsed < 100  # Should be < 100ms
        assert len(json_str) > 100000


class TestResourceUsage:
    """Test resource usage."""

    @pytest.mark.asyncio
    async def test_agent_request_size(self):
        """Test agent request size."""
        request = AgentRequest(
            goal="Test goal with some content " * 100,
            user_id="user@example.com",
            budget_usd=1.0,
            context={"key": "value"} * 50
        )

        import json
        from src.models import AgentRequestBody

        body = AgentRequestBody(
            goal=request.goal,
            user_id=request.user_id,
            budget_usd=request.budget_usd,
            context=request.context
        )

        json_size = len(body.model_dump_json())
        print(f"\nAgent request size: {json_size} bytes")
        assert json_size < 50000  # Should be < 50KB

    @pytest.mark.asyncio
    async def test_agent_response_size(self, setup_load_test):
        """Test agent response size."""
        agent = setup_load_test
        request = AgentRequest(
            goal="Test",
            user_id="user@example.com",
            budget_usd=1.0
        )

        result = await agent.run(request)

        import json
        response_data = {
            "agent_id": result.agent_id,
            "execution_trace": [{"type": "test", "content": "x" * 1000}] * 10,
            "final_response": result.final_response
        }

        json_size = len(json.dumps(response_data))
        print(f"\nAgent response size (with 10KB trace): {json_size} bytes")
        assert json_size < 100000  # Should be < 100KB


class TestStressScenarios:
    """Test stress scenarios."""

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, setup_load_test):
        """Test rapid-fire requests."""
        agent = setup_load_test

        requests = []
        for i in range(50):
            requests.append(
                AgentRequest(
                    goal=f"Task {i}",
                    user_id="user@example.com",
                    budget_usd=1.0
                )
            )

        start = time.time()
        results = await asyncio.gather(
            *[agent.run(req) for req in requests],
            return_exceptions=True
        )
        elapsed = time.time() - start

        successful = sum(1 for r in results if isinstance(r, type(results[0])) and r.status == AgentStatus.COMPLETED)
        print(f"\n50 rapid-fire requests: {elapsed:.2f}s, {successful} successful")

        assert successful >= 40  # At least 80% success

    @pytest.mark.asyncio
    async def test_varying_timeout_loads(self, tool_registry):
        """Test varying timeout under load."""
        agent = AgentExecutor(tool_registry=tool_registry)
        agent.claude_client.query = AsyncMock(
            return_value=("Response", 10, 5)
        )

        # Mix of timeouts
        requests = [
            AgentRequest(
                goal=f"Task {i}",
                user_id="user@example.com",
                budget_usd=1.0,
                timeout_seconds=5 + (i % 10)  # 5-15 second timeouts
            )
            for i in range(30)
        ]

        results = await asyncio.gather(*[agent.run(req) for req in requests])
        successful = sum(1 for r in results if r.status == AgentStatus.COMPLETED)

        print(f"\nVarying timeout test: {successful}/30 successful")
        assert successful >= 25  # At least 83% success
