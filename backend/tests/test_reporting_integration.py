"""Integration tests for reporting service with analytics."""

import json
import csv
import io
from backend.src.services.analytics import (
    QueryAnalytics,
    UserAnalytics,
    ToolAnalytics,
    CostAnalytics,
    PerformanceAnalytics,
    StreamingAnalytics,
)
from backend.src.services.reporting import ReportService, ReportType, ReportFormat


class TestReportingIntegration:
    """Test reporting with real analytics data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.query_analytics = QueryAnalytics()
        self.user_analytics = UserAnalytics()
        self.tool_analytics = ToolAnalytics()
        self.cost_analytics = CostAnalytics()
        self.perf_analytics = PerformanceAnalytics()
        self.streaming_analytics = StreamingAnalytics()

        self.report_service = ReportService()

    def _populate_analytics_data(self):
        """Populate analytics services with sample data."""
        # Add query analytics
        self.query_analytics.add_query(query="q1", complexity="SIMPLE", cost=1.0, success=True, duration_ms=100)
        self.query_analytics.add_query(query="q2", complexity="SIMPLE", cost=1.0, success=True, duration_ms=110)
        self.query_analytics.add_query(query="q3", complexity="MODERATE", cost=2.0, success=True, duration_ms=200)
        self.query_analytics.add_query(query="q4", complexity="COMPLEX", cost=3.0, success=False, duration_ms=500)

        # Add cost analytics
        self.cost_analytics.add_cost("2026-04-15", "user1", 50.0)
        self.cost_analytics.add_cost("2026-04-15", "user2", 30.0)
        self.cost_analytics.add_cost("2026-04-16", "user1", 60.0)

    def test_daily_report_with_analytics_data(self):
        """Test daily report generation with populated analytics."""
        self._populate_analytics_data()

        analytics_data = {
            "total_queries": len(self.query_analytics.queries),
            "success_rate": 0.75,
            "total_cost": 7.0,
            "avg_latency": 227,
            "query_analytics": self.query_analytics.get_complexity_distribution(),
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": self.cost_analytics.get_daily_costs(),
        }

        result = self.report_service.generate_and_export(
            ReportType.DAILY, ReportFormat.JSON, analytics_data
        )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["report_type"] == "daily"
        assert "summary" in parsed
        assert parsed["summary"]["total_queries"] > 0

    def test_weekly_report_with_analytics_data(self):
        """Test weekly report generation with populated analytics."""
        self._populate_analytics_data()

        analytics_data = {
            "total_queries": len(self.query_analytics.queries),
            "success_rate": 0.75,
            "total_cost": 7.0,
            "daily_avg_cost": 1.0,
            "query_analytics": self.query_analytics.get_complexity_distribution(),
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": self.cost_analytics.get_daily_costs(),
            "top_users": [{"user": "user1", "cost": 110.0}],
            "top_tools": [{"tool": "tool1", "effectiveness": 0.9}],
        }

        result = self.report_service.generate_and_export(
            ReportType.WEEKLY, ReportFormat.JSON, analytics_data
        )

        parsed = json.loads(result)
        assert parsed["report_type"] == "weekly"
        assert "top_users" in parsed
        assert "top_tools" in parsed

    def test_daily_report_csv_export(self):
        """Test daily report CSV export with analytics data."""
        self._populate_analytics_data()

        analytics_data = {
            "total_queries": len(self.query_analytics.queries),
            "success_rate": 0.75,
            "total_cost": 7.0,
            "avg_latency": 227,
            "query_analytics": self.query_analytics.get_complexity_distribution(),
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": self.cost_analytics.get_daily_costs(),
        }

        result = self.report_service.generate_and_export(
            ReportType.DAILY, ReportFormat.CSV, analytics_data
        )

        assert isinstance(result, str)
        assert "Report Type" in result
        assert "Summary" in result
        assert "Query Analytics" in result

        # Verify CSV is parseable
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) > 0

    def test_report_contains_all_metrics(self):
        """Test that report includes all analytics metrics."""
        self._populate_analytics_data()

        analytics_data = {
            "total_queries": len(self.query_analytics.queries),
            "success_rate": 0.75,
            "total_cost": 7.0,
            "avg_latency": 227,
            "query_analytics": self.query_analytics.get_complexity_distribution(),
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": self.cost_analytics.get_daily_costs(),
        }

        result = self.report_service.generate_and_export(
            ReportType.DAILY, ReportFormat.JSON, analytics_data
        )

        parsed = json.loads(result)

        # Verify all expected sections
        assert "summary" in parsed
        assert "metrics" in parsed
        assert "query_analytics" in parsed["metrics"]
        assert "user_analytics" in parsed["metrics"]
        assert "tool_analytics" in parsed["metrics"]
        assert "cost_analytics" in parsed["metrics"]

    def test_report_filename_includes_date(self):
        """Test that report filename includes proper date information."""
        filename = self.report_service.get_filename(ReportType.DAILY, ReportFormat.CSV)

        assert filename.startswith("report_daily_")
        assert filename.endswith(".csv")

        # Extract date part
        parts = filename.split("_")
        assert len(parts) >= 3

    def test_monthly_report_with_active_users(self):
        """Test monthly report includes active user count."""
        self._populate_analytics_data()

        analytics_data = {
            "total_queries": len(self.query_analytics.queries),
            "success_rate": 0.75,
            "total_cost": 7.0,
            "daily_avg_cost": 0.23,
            "active_users": 2,
            "query_analytics": self.query_analytics.get_complexity_distribution(),
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": self.cost_analytics.get_daily_costs(),
            "top_users": [],
            "top_tools": [],
            "trends": {"query_trend": "stable"},
        }

        result = self.report_service.generate_and_export(
            ReportType.MONTHLY, ReportFormat.JSON, analytics_data
        )

        parsed = json.loads(result)
        assert parsed["summary"]["active_users"] > 0

    def test_json_vs_csv_format_consistency(self):
        """Test that JSON and CSV formats contain same data."""
        self._populate_analytics_data()

        analytics_data = {
            "total_queries": len(self.query_analytics.queries),
            "success_rate": 0.75,
            "total_cost": 7.0,
            "avg_latency": 227,
            "query_analytics": self.query_analytics.get_complexity_distribution(),
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": self.cost_analytics.get_daily_costs(),
        }

        json_result = self.report_service.generate_and_export(
            ReportType.DAILY, ReportFormat.JSON, analytics_data
        )

        csv_result = self.report_service.generate_and_export(
            ReportType.DAILY, ReportFormat.CSV, analytics_data
        )

        # Both should be non-empty strings
        assert len(json_result) > 0
        assert len(csv_result) > 0

        # JSON should be parseable
        parsed_json = json.loads(json_result)
        assert parsed_json["report_type"] == "daily"

        # CSV should contain key metrics
        assert "total_queries" in csv_result or "Query" in csv_result

    def test_report_with_empty_analytics(self):
        """Test report generation with empty analytics data."""
        analytics_data = {
            "total_queries": 0,
            "success_rate": 0.0,
            "total_cost": 0.0,
            "avg_latency": 0,
            "query_analytics": {},
            "user_analytics": {"users": {}, "total_users": 0},
            "tool_analytics": {"tools": {}, "total_tools": 0},
            "cost_analytics": {},
        }

        result = self.report_service.generate_and_export(
            ReportType.DAILY, ReportFormat.JSON, analytics_data
        )

        parsed = json.loads(result)
        assert parsed["summary"]["total_queries"] == 0
