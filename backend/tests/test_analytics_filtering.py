"""Tests for analytics filtering functionality."""

import pytest
from backend.src.services.analytics import QueryAnalytics, CostAnalytics


class TestQueryAnalyticsFiltering:
    """Test query filtering with multiple dimensions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analytics = QueryAnalytics()

        # Add various queries
        self.analytics.add_query("q1", "SIMPLE", True, 1.0, 100)
        self.analytics.add_query("q2", "SIMPLE", True, 1.5, 110)
        self.analytics.add_query("q3", "MODERATE", True, 2.0, 200)
        self.analytics.add_query("q4", "MODERATE", False, 2.5, 210)
        self.analytics.add_query("q5", "COMPLEX", True, 3.0, 300)
        self.analytics.add_query("q6", "COMPLEX", False, 3.5, 310)

    def test_filter_by_complexity_single(self):
        """Test filtering by single complexity level."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            complexities=["SIMPLE"],
        )

        assert total == 2
        assert len(queries) == 2
        assert all(q["complexity"] == "SIMPLE" for q in queries)

    def test_filter_by_complexity_multiple(self):
        """Test filtering by multiple complexity levels."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            complexities=["SIMPLE", "COMPLEX"],
        )

        assert total == 4
        assert len(queries) == 4
        assert all(q["complexity"] in ["SIMPLE", "COMPLEX"] for q in queries)

    def test_filter_by_success_status_success(self):
        """Test filtering for successful queries only."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            success_status="success",
        )

        assert total == 4
        assert len(queries) == 4
        assert all(q["success"] for q in queries)

    def test_filter_by_success_status_failed(self):
        """Test filtering for failed queries only."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            success_status="failed",
        )

        assert total == 2
        assert len(queries) == 2
        assert all(not q["success"] for q in queries)

    def test_filter_by_cost_range(self):
        """Test filtering by cost range."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            cost_min=1.5,
            cost_max=2.5,
        )

        assert total == 3
        assert all(1.5 <= q["cost"] <= 2.5 for q in queries)

    def test_filter_by_latency_range(self):
        """Test filtering by latency range."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            latency_min=200,
            latency_max=310,
        )

        assert total == 4
        assert all(200 <= q["duration_ms"] <= 310 for q in queries)

    def test_filter_combined(self):
        """Test filtering with multiple dimensions combined."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            complexities=["SIMPLE", "MODERATE"],
            success_status="success",
            cost_min=1.0,
            cost_max=2.5,
        )

        assert total == 3
        assert all(q["complexity"] in ["SIMPLE", "MODERATE"] for q in queries)
        assert all(q["success"] for q in queries)
        assert all(1.0 <= q["cost"] <= 2.5 for q in queries)

    def test_sort_by_cost_descending(self):
        """Test sorting by cost descending."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            sort_by="cost",
            sort_order="desc",
        )

        costs = [q["cost"] for q in queries]
        assert costs == sorted(costs, reverse=True)

    def test_sort_by_cost_ascending(self):
        """Test sorting by cost ascending."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            sort_by="cost",
            sort_order="asc",
        )

        costs = [q["cost"] for q in queries]
        assert costs == sorted(costs)

    def test_sort_by_latency(self):
        """Test sorting by latency."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            sort_by="latency",
            sort_order="desc",
        )

        latencies = [q["duration_ms"] for q in queries]
        assert latencies == sorted(latencies, reverse=True)

    def test_pagination_limit(self):
        """Test pagination with limit."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            limit=3,
        )

        assert len(queries) == 3
        assert total == 6

    def test_pagination_offset(self):
        """Test pagination with offset."""
        queries1, total1 = self.analytics.filter_queries(
            hours=24,
            limit=2,
            offset=0,
        )

        queries2, total2 = self.analytics.filter_queries(
            hours=24,
            limit=2,
            offset=2,
        )

        assert len(queries1) == 2
        assert len(queries2) == 2
        assert queries1[0] != queries2[0]
        assert total1 == total2 == 6

    def test_empty_filter_result(self):
        """Test filter that returns no results."""
        queries, total = self.analytics.filter_queries(
            hours=24,
            complexities=["NONEXISTENT"],
        )

        assert total == 0
        assert len(queries) == 0


class TestCostAnalyticsFiltering:
    """Test cost filtering functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analytics = CostAnalytics()

        # Add costs for different users
        self.analytics.add_cost("2026-04-15", "user1", 50.0)
        self.analytics.add_cost("2026-04-15", "user2", 30.0)
        self.analytics.add_cost("2026-04-16", "user1", 60.0)
        self.analytics.add_cost("2026-04-16", "user2", 40.0)
        self.analytics.add_cost("2026-04-17", "user3", 25.0)

    def test_filter_users_by_cost_range(self):
        """Test filtering users by cost range."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            cost_min=50,
            cost_max=150,
        )

        assert total == 2
        assert all(50 <= u["cost"] <= 150 for u in users)

    def test_filter_users_cost_min_only(self):
        """Test filtering with minimum cost only."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            cost_min=80,
        )

        assert total == 1
        assert all(u["cost"] >= 80 for u in users)

    def test_filter_users_cost_max_only(self):
        """Test filtering with maximum cost only."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            cost_max=80,
        )

        assert total == 2
        assert all(u["cost"] <= 80 for u in users)

    def test_sort_users_by_cost_desc(self):
        """Test sorting users by cost descending."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            sort_by="cost",
            sort_order="desc",
        )

        costs = [u["cost"] for u in users]
        assert costs == sorted(costs, reverse=True)

    def test_sort_users_by_cost_asc(self):
        """Test sorting users by cost ascending."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            sort_by="cost",
            sort_order="asc",
        )

        costs = [u["cost"] for u in users]
        assert costs == sorted(costs)

    def test_sort_users_by_name(self):
        """Test sorting users by name."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            sort_by="user",
            sort_order="asc",
        )

        user_ids = [u["user"] for u in users]
        assert user_ids == sorted(user_ids)

    def test_pagination_users(self):
        """Test pagination for users."""
        users1, total1 = self.analytics.filter_users_by_cost(
            days=30,
            limit=2,
            offset=0,
        )

        users2, total2 = self.analytics.filter_users_by_cost(
            days=30,
            limit=2,
            offset=2,
        )

        assert len(users1) == 2
        assert len(users2) == 1
        assert total1 == total2 == 3

    def test_filter_by_date_range(self):
        """Test filtering by date range (using days parameter)."""
        users1, total1 = self.analytics.filter_users_by_cost(days=30)
        users2, total2 = self.analytics.filter_users_by_cost(days=1)

        assert total1 == 3  # All users in 30 days
        assert total2 <= 3  # Fewer users in 1 day

    def test_combined_filter_and_sort(self):
        """Test combined filtering and sorting."""
        users, total = self.analytics.filter_users_by_cost(
            days=30,
            cost_min=30,
            cost_max=120,
            sort_by="cost",
            sort_order="asc",
        )

        assert all(30 <= u["cost"] <= 120 for u in users)
        costs = [u["cost"] for u in users]
        assert costs == sorted(costs)
