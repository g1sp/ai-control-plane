"""Tests for reporting service."""

import json
import csv
import io
from datetime import datetime, timedelta
from backend.src.services.reporting import (
    ReportGenerator,
    ReportExporter,
    ReportService,
    ReportType,
    ReportFormat,
)


class TestReportGenerator:
    """Test report generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ReportGenerator()
        self.sample_data = {
            "total_queries": 1000,
            "success_rate": 0.95,
            "total_cost": 150.50,
            "avg_latency": 245,
            "query_analytics": {"SIMPLE": 500, "MODERATE": 300, "COMPLEX": 150, "VERY_COMPLEX": 50},
            "user_analytics": {
                "user1": {"query_count": 300, "total_cost": 50.0, "avg_cost": 0.167},
                "user2": {"query_count": 200, "total_cost": 35.0, "avg_cost": 0.175},
            },
            "tool_analytics": {
                "tool1": {"effectiveness": 0.92, "success_rate": 0.98, "usage_count": 400, "avg_duration_ms": 120},
                "tool2": {"effectiveness": 0.88, "success_rate": 0.95, "usage_count": 300, "avg_duration_ms": 150},
            },
            "cost_analytics": {"2026-04-10": 50.0, "2026-04-11": 55.0, "2026-04-12": 45.5},
            "daily_avg_cost": 50.17,
            "top_users": [("user1", 50.0), ("user2", 35.0)],
            "top_tools": [
                {"name": "tool1", "effectiveness": 0.92},
                {"name": "tool2", "effectiveness": 0.88},
            ],
            "trends": {"query_trend": "stable", "cost_trend": "increasing"},
        }

    def test_generate_daily_report(self):
        """Test daily report generation."""
        report = self.generator.generate_daily_report(self.sample_data)

        assert report["report_type"] == ReportType.DAILY.value
        assert "date" in report
        assert report["generated_at"] is not None
        assert report["summary"]["total_queries"] == 1000
        assert report["summary"]["success_rate"] == 0.95
        assert report["summary"]["total_cost"] == 150.50
        assert report["metrics"]["query_analytics"] == self.sample_data["query_analytics"]

    def test_generate_daily_report_with_date(self):
        """Test daily report with specific date."""
        date = "2026-04-15"
        report = self.generator.generate_daily_report(self.sample_data, date=date)

        assert report["date"] == date
        assert report["report_type"] == ReportType.DAILY.value

    def test_generate_weekly_report(self):
        """Test weekly report generation."""
        report = self.generator.generate_weekly_report(self.sample_data)

        assert report["report_type"] == ReportType.WEEKLY.value
        assert "period" in report
        assert "to" in report["period"]
        assert "top_users" in report
        assert "top_tools" in report
        assert report["summary"]["avg_success_rate"] == 0.95

    def test_generate_weekly_report_with_end_date(self):
        """Test weekly report with specific end date."""
        end_date = "2026-04-15"
        report = self.generator.generate_weekly_report(self.sample_data, end_date=end_date)

        assert end_date in report["period"]
        assert report["report_type"] == ReportType.WEEKLY.value

    def test_generate_monthly_report(self):
        """Test monthly report generation."""
        report = self.generator.generate_monthly_report(self.sample_data)

        assert report["report_type"] == ReportType.MONTHLY.value
        assert "period" in report
        assert "trends" in report
        assert "top_users" in report
        assert "top_tools" in report
        assert report["summary"]["active_users"] == 0

    def test_generate_monthly_report_with_end_date(self):
        """Test monthly report with specific end date."""
        end_date = "2026-04-15"
        report = self.generator.generate_monthly_report(self.sample_data, end_date=end_date)

        assert end_date in report["period"]
        assert report["report_type"] == ReportType.MONTHLY.value


class TestReportExporter:
    """Test report export formats."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = ReportExporter()
        self.sample_report = {
            "report_type": "daily",
            "date": "2026-04-15",
            "generated_at": "2026-04-15T10:30:00",
            "summary": {
                "total_queries": 1000,
                "success_rate": 0.95,
                "total_cost": 150.50,
                "avg_latency_ms": 245,
            },
            "metrics": {
                "query_analytics": {"SIMPLE": 500, "MODERATE": 300},
                "user_analytics": {"user1": 50.0, "user2": 35.0},
                "tool_analytics": {},
                "cost_analytics": {},
            },
            "top_users": [
                {"user": "user1", "cost": 50.0},
                {"user": "user2", "cost": 35.0},
            ],
        }

    def test_export_to_json(self):
        """Test JSON export."""
        json_str = self.exporter.to_json(self.sample_report)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["report_type"] == "daily"
        assert parsed["summary"]["total_queries"] == 1000

    def test_export_to_csv(self):
        """Test CSV export."""
        csv_str = self.exporter.to_csv(self.sample_report)

        assert isinstance(csv_str, str)
        lines = csv_str.strip().split("\n")
        assert len(lines) > 0
        assert "Report Type" in csv_str
        assert "daily" in csv_str

    def test_csv_structure(self):
        """Test CSV has proper structure."""
        csv_str = self.exporter.to_csv(self.sample_report)

        assert "Summary" in csv_str
        assert "Query Analytics" in csv_str
        assert "User Analytics" in csv_str
        assert "Top Users" in csv_str

    def test_export_with_nested_metrics(self):
        """Test export with nested metric objects."""
        report = self.sample_report.copy()
        report["metrics"]["user_analytics"] = {
            "user1": {"query_count": 300, "total_cost": 50.0},
            "user2": {"query_count": 200, "total_cost": 35.0},
        }

        csv_str = self.exporter.to_csv(report)
        assert "user1" in csv_str
        assert "query_count" in csv_str

    def test_export_empty_report(self):
        """Test export with minimal report."""
        minimal_report = {
            "report_type": "daily",
            "generated_at": datetime.utcnow().isoformat(),
        }

        json_str = self.exporter.to_json(minimal_report)
        assert "report_type" in json_str

        csv_str = self.exporter.to_csv(minimal_report)
        assert "Report Type" in csv_str


class TestReportService:
    """Test high-level reporting service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ReportService()
        self.sample_data = {
            "total_queries": 1000,
            "success_rate": 0.95,
            "total_cost": 150.50,
            "avg_latency": 245,
            "query_analytics": {"SIMPLE": 500, "MODERATE": 300},
            "user_analytics": {"user1": 50.0},
            "tool_analytics": {},
            "cost_analytics": {},
        }

    def test_generate_and_export_json(self):
        """Test generate and export to JSON."""
        result = self.service.generate_and_export(
            ReportType.DAILY, ReportFormat.JSON, self.sample_data
        )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "report_type" in parsed
        assert parsed["report_type"] == "daily"

    def test_generate_and_export_csv(self):
        """Test generate and export to CSV."""
        result = self.service.generate_and_export(
            ReportType.DAILY, ReportFormat.CSV, self.sample_data
        )

        assert isinstance(result, str)
        assert "Report Type" in result

    def test_generate_weekly_json(self):
        """Test weekly report as JSON."""
        result = self.service.generate_and_export(
            ReportType.WEEKLY, ReportFormat.JSON, self.sample_data
        )

        parsed = json.loads(result)
        assert parsed["report_type"] == "weekly"

    def test_generate_monthly_csv(self):
        """Test monthly report as CSV."""
        result = self.service.generate_and_export(
            ReportType.MONTHLY, ReportFormat.CSV, self.sample_data
        )

        assert isinstance(result, str)
        assert "Report Type" in result

    def test_get_filename_daily(self):
        """Test filename generation for daily report."""
        filename = self.service.get_filename(ReportType.DAILY, ReportFormat.JSON)

        assert filename.startswith("report_daily_")
        assert filename.endswith(".json")

    def test_get_filename_weekly(self):
        """Test filename generation for weekly report."""
        filename = self.service.get_filename(ReportType.WEEKLY, ReportFormat.CSV)

        assert filename.startswith("report_weekly_")
        assert filename.endswith(".csv")

    def test_get_filename_monthly(self):
        """Test filename generation for monthly report."""
        filename = self.service.get_filename(ReportType.MONTHLY, ReportFormat.JSON)

        assert filename.startswith("report_monthly_")
        assert filename.endswith(".json")

    def test_get_filename_with_custom_date(self):
        """Test filename generation with custom date suffix."""
        filename = self.service.get_filename(ReportType.DAILY, ReportFormat.JSON, date_suffix="20260415")

        assert "20260415" in filename

    def test_generate_and_export_with_kwargs(self):
        """Test generate and export with additional parameters."""
        result = self.service.generate_and_export(
            ReportType.DAILY,
            ReportFormat.JSON,
            self.sample_data,
            date="2026-04-15",
        )

        parsed = json.loads(result)
        assert parsed["date"] == "2026-04-15"

    def test_csv_export_parseable(self):
        """Test exported CSV can be parsed."""
        result = self.service.generate_and_export(
            ReportType.DAILY, ReportFormat.CSV, self.sample_data
        )

        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) > 0

    def test_json_export_complete_structure(self):
        """Test JSON export has complete structure."""
        result = self.service.generate_and_export(
            ReportType.WEEKLY, ReportFormat.JSON, self.sample_data
        )

        parsed = json.loads(result)
        assert "report_type" in parsed
        assert "period" in parsed
        assert "generated_at" in parsed
        assert "summary" in parsed
        assert "metrics" in parsed
