"""Tests for analytics service."""

import pytest
from datetime import datetime, timedelta
from src.services.analytics import (
    QueryAnalytics,
    UserAnalytics,
    ToolAnalytics,
    CostAnalytics,
    PerformanceAnalytics,
    StreamingAnalytics,
    get_query_analytics,
    get_user_analytics,
    get_tool_analytics,
    get_cost_analytics,
    get_performance_analytics,
    get_streaming_analytics,
)


class TestQueryAnalytics:
    """Test query analytics."""

    def setup_method(self):
        """Setup analytics."""
        self.analytics = QueryAnalytics()

    def test_add_and_get_complexity_distribution(self):
        """Test complexity distribution."""
        self.analytics.add_query("What is AI?", "SIMPLE", True, 0.01, 100)
        self.analytics.add_query("Design a system", "COMPLEX", True, 0.05, 500)
        self.analytics.add_query("Compare A and B", "MODERATE", True, 0.02, 200)

        dist = self.analytics.get_complexity_distribution(hours=24)

        assert dist["SIMPLE"] == 1
        assert dist["MODERATE"] == 1
        assert dist["COMPLEX"] == 1

    def test_success_rate(self):
        """Test success rate calculation."""
        for i in range(10):
            self.analytics.add_query(f"Query {i}", "SIMPLE", True, 0.01, 100)

        # Add 5 failures
        for i in range(5):
            self.analytics.add_query(f"Query fail {i}", "SIMPLE", False, 0.01, 100)

        success_rate = self.analytics.get_success_rate(hours=24)
        assert success_rate == pytest.approx(0.667, abs=0.01)

    def test_avg_latency_by_complexity(self):
        """Test average latency by complexity."""
        self.analytics.add_query("Q1", "SIMPLE", True, 0.01, 100)
        self.analytics.add_query("Q2", "SIMPLE", True, 0.01, 200)
        self.analytics.add_query("Q3", "COMPLEX", True, 0.05, 400)
        self.analytics.add_query("Q4", "COMPLEX", True, 0.05, 600)

        latencies = self.analytics.get_avg_latency_by_complexity(hours=24)

        assert latencies["SIMPLE"] == 150.0
        assert latencies["COMPLEX"] == 500.0

    def test_total_cost(self):
        """Test total cost calculation."""
        self.analytics.add_query("Q1", "SIMPLE", True, 0.015, 100)
        self.analytics.add_query("Q2", "MODERATE", True, 0.025, 200)
        self.analytics.add_query("Q3", "COMPLEX", True, 0.035, 300)

        total = self.analytics.get_total_cost(hours=24)
        assert total == pytest.approx(0.075, abs=0.001)

    def test_avg_cost_per_query(self):
        """Test average cost per query."""
        self.analytics.add_query("Q1", "SIMPLE", True, 0.015, 100)
        self.analytics.add_query("Q2", "SIMPLE", True, 0.025, 200)

        avg = self.analytics.get_avg_cost_per_query(hours=24)
        assert avg == pytest.approx(0.02, abs=0.001)

    def test_empty_analytics(self):
        """Test with no data."""
        assert self.analytics.get_complexity_distribution() == {}
        assert self.analytics.get_success_rate() == 1.0
        assert self.analytics.get_total_cost() == 0.0
        assert self.analytics.get_avg_cost_per_query() == 0.0


class TestUserAnalytics:
    """Test user analytics."""

    def setup_method(self):
        """Setup analytics."""
        self.analytics = UserAnalytics()

    def test_add_and_get_user_metrics(self):
        """Test user metrics."""
        self.analytics.add_user_query("user1@example.com", 5, 0.05, "search")
        self.analytics.add_user_query("user1@example.com", 3, 0.03, "calculator")

        metrics = self.analytics.get_user_metrics("user1@example.com", hours=24)

        assert metrics["query_count"] == 8
        assert metrics["total_cost"] == pytest.approx(0.08, abs=0.001)
        assert metrics["avg_cost"] == pytest.approx(0.04, abs=0.001)

    def test_get_all_users_metrics(self):
        """Test metrics for all users."""
        self.analytics.add_user_query("user1@example.com", 5, 0.05, "search")
        self.analytics.add_user_query("user2@example.com", 3, 0.03, "calculator")

        all_metrics = self.analytics.get_all_users_metrics(hours=24)

        assert "user1@example.com" in all_metrics
        assert "user2@example.com" in all_metrics
        assert all_metrics["user1@example.com"]["total_cost"] == pytest.approx(0.05, abs=0.001)
        assert all_metrics["user2@example.com"]["total_cost"] == pytest.approx(0.03, abs=0.001)

    def test_user_spending_trend(self):
        """Test spending trend over days."""
        self.analytics.add_user_query("user1@example.com", 5, 0.05, "search")
        # Simulate yesterday's query (would need mocking in real tests)
        self.analytics.add_user_query("user1@example.com", 3, 0.03, "calculator")

        trend = self.analytics.get_user_spending_trend("user1@example.com", days=7)

        # All queries are today, so should have one date entry
        assert len(trend) == 1
        total_cost = sum(trend.values())
        assert total_cost == pytest.approx(0.08, abs=0.001)

    def test_top_users_by_spending(self):
        """Test top spenders."""
        self.analytics.add_user_query("user1@example.com", 5, 0.50, "search")
        self.analytics.add_user_query("user2@example.com", 3, 0.30, "calculator")
        self.analytics.add_user_query("user3@example.com", 2, 0.10, "analytics")

        top = self.analytics.get_top_users_by_spending(hours=24, limit=2)

        assert len(top) == 2
        assert top[0][0] == "user1@example.com"
        assert top[0][1] == pytest.approx(0.50, abs=0.001)
        assert top[1][0] == "user2@example.com"


class TestToolAnalytics:
    """Test tool analytics."""

    def setup_method(self):
        """Setup analytics."""
        self.analytics = ToolAnalytics()

    def test_add_and_get_tool_stats(self):
        """Test tool statistics."""
        self.analytics.add_tool_use("search", True, 150, 500, 0.85)
        self.analytics.add_tool_use("search", True, 160, 520, 0.84)

        stats = self.analytics.get_tool_stats("search", hours=24)

        assert stats["uses"] == 2
        assert stats["successes"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["avg_tokens"] == pytest.approx(155, abs=1)
        assert stats["avg_effectiveness"] == pytest.approx(0.845, abs=0.01)

    def test_tool_effectiveness_with_failures(self):
        """Test effectiveness with failed uses."""
        self.analytics.add_tool_use("calculator", True, 100, 300, 0.9)
        self.analytics.add_tool_use("calculator", False, 200, 1000, 0.2)

        stats = self.analytics.get_tool_stats("calculator", hours=24)

        assert stats["success_rate"] == 0.5
        assert stats["avg_effectiveness"] == pytest.approx(0.55, abs=0.01)

    def test_get_all_tools_stats(self):
        """Test all tools statistics."""
        self.analytics.add_tool_use("search", True, 150, 500, 0.85)
        self.analytics.add_tool_use("calculator", True, 100, 300, 0.80)

        all_stats = self.analytics.get_all_tools_stats(hours=24)

        assert "search" in all_stats
        assert "calculator" in all_stats
        assert all_stats["search"]["avg_effectiveness"] == pytest.approx(0.85, abs=0.01)

    def test_tool_rankings(self):
        """Test tool ranking by effectiveness."""
        self.analytics.add_tool_use("search", True, 150, 500, 0.90)
        self.analytics.add_tool_use("calculator", True, 100, 300, 0.70)
        self.analytics.add_tool_use("code_gen", True, 200, 800, 0.80)

        rankings = self.analytics.get_tool_rankings(hours=24)

        assert rankings[0][0] == "search"
        assert rankings[0][1] == pytest.approx(0.90, abs=0.01)
        assert rankings[1][0] == "code_gen"


class TestCostAnalytics:
    """Test cost analytics."""

    def setup_method(self):
        """Setup analytics."""
        self.analytics = CostAnalytics()

    def test_add_and_get_daily_costs(self):
        """Test daily cost tracking."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        self.analytics.add_cost(today, "user1@example.com", 0.05)
        self.analytics.add_cost(today, "user2@example.com", 0.03)

        daily = self.analytics.get_daily_costs(days=1)

        assert daily[today] == pytest.approx(0.08, abs=0.001)

    def test_total_cost(self):
        """Test total cost calculation."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        self.analytics.add_cost(today, "user1@example.com", 0.05)
        self.analytics.add_cost(today, "user2@example.com", 0.03)

        total = self.analytics.get_total_cost(days=30)
        assert total == pytest.approx(0.08, abs=0.001)

    def test_avg_daily_cost(self):
        """Test average daily cost."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        self.analytics.add_cost(today, "user1@example.com", 0.05)
        self.analytics.add_cost(today, "user2@example.com", 0.03)

        avg = self.analytics.get_avg_daily_cost(days=1)
        assert avg == pytest.approx(0.08, abs=0.001)

    def test_forecast_cost(self):
        """Test cost forecasting."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Add daily costs
        self.analytics.add_cost(today, "user1@example.com", 0.10)

        forecast = self.analytics.forecast_cost(days_ahead=7, lookback_days=1)
        assert forecast == pytest.approx(0.70, abs=0.01)

    def test_get_cost_by_user(self):
        """Test cost breakdown by user."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        self.analytics.add_cost(today, "user1@example.com", 0.05)
        self.analytics.add_cost(today, "user2@example.com", 0.03)

        by_user = self.analytics.get_cost_by_user(today)

        assert by_user["user1@example.com"] == pytest.approx(0.05, abs=0.001)
        assert by_user["user2@example.com"] == pytest.approx(0.03, abs=0.001)

    def test_top_cost_users(self):
        """Test top cost users."""
        today = datetime.utcnow().strftime("%Y-%m-%d")

        self.analytics.add_cost(today, "user1@example.com", 0.50)
        self.analytics.add_cost(today, "user2@example.com", 0.30)
        self.analytics.add_cost(today, "user3@example.com", 0.10)

        top = self.analytics.get_top_cost_users(days=30, limit=2)

        assert len(top) == 2
        assert top[0][0] == "user1@example.com"
        assert top[0][1] == pytest.approx(0.50, abs=0.001)


class TestPerformanceAnalytics:
    """Test performance analytics."""

    def setup_method(self):
        """Setup analytics."""
        self.analytics = PerformanceAnalytics()

    def test_add_and_get_latency_percentiles(self):
        """Test latency percentiles."""
        # Add 100 latencies to compute percentiles
        for i in range(100):
            self.analytics.add_latency(i * 10)  # 0, 10, 20, ..., 990

        percentiles = self.analytics.get_latency_percentiles()

        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert percentiles["min"] == 0
        assert percentiles["max"] == 990

    def test_avg_latency(self):
        """Test average latency."""
        self.analytics.add_latency(100)
        self.analytics.add_latency(200)
        self.analytics.add_latency(300)

        avg = self.analytics.get_avg_latency()
        assert avg == pytest.approx(200, abs=1)

    def test_throughput_samples(self):
        """Test throughput tracking."""
        self.analytics.add_throughput_sample("2026-04-16T12:00:00Z", 100)
        self.analytics.add_throughput_sample("2026-04-16T12:01:00Z", 120)

        throughput = self.analytics.get_throughput()

        assert throughput["2026-04-16T12:00:00Z"] == 100
        assert throughput["2026-04-16T12:01:00Z"] == 120

    def test_avg_throughput(self):
        """Test average throughput."""
        self.analytics.add_throughput_sample("2026-04-16T12:00:00Z", 100)
        self.analytics.add_throughput_sample("2026-04-16T12:01:00Z", 200)

        avg = self.analytics.get_avg_throughput()
        assert avg == pytest.approx(150, abs=1)

    def test_empty_latencies(self):
        """Test with no latency data."""
        percentiles = self.analytics.get_latency_percentiles()

        assert percentiles["p50"] == 0.0
        assert percentiles["p95"] == 0.0
        assert self.analytics.get_avg_latency() == 0.0


class TestStreamingAnalytics:
    """Test streaming analytics."""

    def setup_method(self):
        """Setup analytics."""
        self.analytics = StreamingAnalytics()

    def test_add_and_get_session_stats(self):
        """Test session statistics."""
        self.analytics.add_session("session1", True, 5000, 50)
        self.analytics.add_session("session2", True, 6000, 60)
        self.analytics.add_session("session3", False, 2000, 10)

        stats = self.analytics.get_session_stats(hours=24)

        assert stats["total_sessions"] == 3
        assert stats["completed_sessions"] == 2
        assert stats["completion_rate"] == pytest.approx(0.667, abs=0.01)
        assert stats["total_events"] == 120

    def test_completion_rate(self):
        """Test session completion rate."""
        self.analytics.add_session("s1", True, 5000, 50)
        self.analytics.add_session("s2", True, 5000, 50)
        self.analytics.add_session("s3", False, 2000, 10)

        rate = self.analytics.get_session_completion_rate(hours=24)
        assert rate == pytest.approx(0.667, abs=0.01)

    def test_avg_session_duration(self):
        """Test average session duration."""
        self.analytics.add_session("s1", True, 5000, 50)
        self.analytics.add_session("s2", True, 7000, 60)

        avg = self.analytics.get_avg_session_duration(hours=24)
        assert avg == pytest.approx(6000, abs=100)

    def test_avg_events_per_session(self):
        """Test average events per session."""
        self.analytics.add_session("s1", True, 5000, 50)
        self.analytics.add_session("s2", True, 6000, 70)

        avg = self.analytics.get_avg_events_per_session(hours=24)
        assert avg == pytest.approx(60, abs=1)


class TestAnalyticsSingletons:
    """Test global analytics singletons."""

    def test_get_query_analytics(self):
        """Test getting query analytics singleton."""
        qa1 = get_query_analytics()
        qa2 = get_query_analytics()
        assert qa1 is qa2

    def test_get_user_analytics(self):
        """Test getting user analytics singleton."""
        ua1 = get_user_analytics()
        ua2 = get_user_analytics()
        assert ua1 is ua2

    def test_get_tool_analytics(self):
        """Test getting tool analytics singleton."""
        ta1 = get_tool_analytics()
        ta2 = get_tool_analytics()
        assert ta1 is ta2

    def test_get_cost_analytics(self):
        """Test getting cost analytics singleton."""
        ca1 = get_cost_analytics()
        ca2 = get_cost_analytics()
        assert ca1 is ca2

    def test_get_performance_analytics(self):
        """Test getting performance analytics singleton."""
        pa1 = get_performance_analytics()
        pa2 = get_performance_analytics()
        assert pa1 is pa2

    def test_get_streaming_analytics(self):
        """Test getting streaming analytics singleton."""
        sa1 = get_streaming_analytics()
        sa2 = get_streaming_analytics()
        assert sa1 is sa2
