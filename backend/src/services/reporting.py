"""Reporting service for generating and exporting reports."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import csv
import io
import json


class ReportFormat(str, Enum):
    """Report export format."""
    CSV = "csv"
    JSON = "json"


class ReportType(str, Enum):
    """Report type."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportGenerator:
    """Generate reports from analytics data."""

    def __init__(self):
        """Initialize report generator."""
        pass

    def generate_daily_report(
        self,
        analytics_data: Dict[str, Any],
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate daily report."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        return {
            "report_type": ReportType.DAILY.value,
            "date": date,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_queries": analytics_data.get("total_queries", 0),
                "success_rate": analytics_data.get("success_rate", 0.0),
                "total_cost": analytics_data.get("total_cost", 0.0),
                "avg_latency_ms": analytics_data.get("avg_latency", 0),
            },
            "metrics": {
                "query_analytics": analytics_data.get("query_analytics", {}),
                "user_analytics": analytics_data.get("user_analytics", {}),
                "tool_analytics": analytics_data.get("tool_analytics", {}),
                "cost_analytics": analytics_data.get("cost_analytics", {}),
            },
        }

    def generate_weekly_report(
        self,
        analytics_data: Dict[str, Any],
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate weekly report."""
        if end_date is None:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")

        end = datetime.strptime(end_date, "%Y-%m-%d")
        start = (end - timedelta(days=7)).strftime("%Y-%m-%d")

        return {
            "report_type": ReportType.WEEKLY.value,
            "period": f"{start} to {end_date}",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_queries": analytics_data.get("total_queries", 0),
                "avg_success_rate": analytics_data.get("success_rate", 0.0),
                "total_cost": analytics_data.get("total_cost", 0.0),
                "daily_average_cost": analytics_data.get("daily_avg_cost", 0.0),
            },
            "metrics": {
                "query_analytics": analytics_data.get("query_analytics", {}),
                "user_analytics": analytics_data.get("user_analytics", {}),
                "tool_analytics": analytics_data.get("tool_analytics", {}),
                "cost_analytics": analytics_data.get("cost_analytics", {}),
            },
            "top_users": analytics_data.get("top_users", []),
            "top_tools": analytics_data.get("top_tools", []),
        }

    def generate_monthly_report(
        self,
        analytics_data: Dict[str, Any],
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate monthly report."""
        if end_date is None:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")

        end = datetime.strptime(end_date, "%Y-%m-%d")
        start = (end - timedelta(days=30)).strftime("%Y-%m-%d")

        return {
            "report_type": ReportType.MONTHLY.value,
            "period": f"{start} to {end_date}",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_queries": analytics_data.get("total_queries", 0),
                "avg_success_rate": analytics_data.get("success_rate", 0.0),
                "total_cost": analytics_data.get("total_cost", 0.0),
                "daily_average_cost": analytics_data.get("daily_avg_cost", 0.0),
                "active_users": analytics_data.get("active_users", 0),
            },
            "metrics": {
                "query_analytics": analytics_data.get("query_analytics", {}),
                "user_analytics": analytics_data.get("user_analytics", {}),
                "tool_analytics": analytics_data.get("tool_analytics", {}),
                "cost_analytics": analytics_data.get("cost_analytics", {}),
            },
            "top_users": analytics_data.get("top_users", []),
            "top_tools": analytics_data.get("top_tools", []),
            "trends": analytics_data.get("trends", {}),
        }


class ReportExporter:
    """Export reports in various formats."""

    @staticmethod
    def to_json(report: Dict[str, Any]) -> str:
        """Export report as JSON."""
        return json.dumps(report, indent=2, default=str)

    @staticmethod
    def to_csv(report: Dict[str, Any]) -> str:
        """Export report as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Report Type", report.get("report_type", "N/A")])
        if "date" in report:
            writer.writerow(["Date", report["date"]])
        if "period" in report:
            writer.writerow(["Period", report["period"]])
        writer.writerow(["Generated", report.get("generated_at", "N/A")])
        writer.writerow([])

        # Summary
        writer.writerow(["Summary"])
        summary = report.get("summary", {})
        for key, value in summary.items():
            writer.writerow([key, value])
        writer.writerow([])

        # Metrics - Query Analytics
        writer.writerow(["Query Analytics"])
        query_analytics = report.get("metrics", {}).get("query_analytics", {})
        for key, value in query_analytics.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    writer.writerow([f"{key}.{sub_key}", sub_value])
            else:
                writer.writerow([key, value])
        writer.writerow([])

        # Metrics - User Analytics
        writer.writerow(["User Analytics"])
        user_analytics = report.get("metrics", {}).get("user_analytics", {})
        for key, value in user_analytics.items():
            if isinstance(value, dict):
                writer.writerow([key, ""])
                for sub_key, sub_value in value.items():
                    writer.writerow([f"  {sub_key}", sub_value])
            else:
                writer.writerow([key, value])
        writer.writerow([])

        # Top Users if available
        if "top_users" in report:
            writer.writerow(["Top Users"])
            writer.writerow(["User", "Cost"])
            for user in report["top_users"]:
                if isinstance(user, dict):
                    writer.writerow([user.get("user", ""), user.get("cost", 0)])
            writer.writerow([])

        # Top Tools if available
        if "top_tools" in report:
            writer.writerow(["Top Tools"])
            writer.writerow(["Tool", "Effectiveness"])
            for tool in report["top_tools"]:
                if isinstance(tool, dict):
                    writer.writerow([tool.get("tool", ""), tool.get("effectiveness", 0)])
                else:
                    writer.writerow([tool, ""])
            writer.writerow([])

        return output.getvalue()


class ReportService:
    """High-level reporting service."""

    def __init__(self):
        """Initialize reporting service."""
        self.generator = ReportGenerator()
        self.exporter = ReportExporter()

    def generate_and_export(
        self,
        report_type: ReportType,
        export_format: ReportFormat,
        analytics_data: Dict[str, Any],
        **kwargs
    ) -> str:
        """Generate report and export in specified format."""
        # Generate report
        if report_type == ReportType.DAILY:
            report = self.generator.generate_daily_report(analytics_data, kwargs.get("date"))
        elif report_type == ReportType.WEEKLY:
            report = self.generator.generate_weekly_report(analytics_data, kwargs.get("end_date"))
        elif report_type == ReportType.MONTHLY:
            report = self.generator.generate_monthly_report(analytics_data, kwargs.get("end_date"))
        else:
            report = analytics_data

        # Export report
        if export_format == ReportFormat.JSON:
            return self.exporter.to_json(report)
        elif export_format == ReportFormat.CSV:
            return self.exporter.to_csv(report)
        else:
            return self.exporter.to_json(report)

    def get_filename(
        self,
        report_type: ReportType,
        export_format: ReportFormat,
        date_suffix: Optional[str] = None,
    ) -> str:
        """Get suggested filename for report."""
        if date_suffix is None:
            date_suffix = datetime.utcnow().strftime("%Y%m%d")

        extension = export_format.value
        return f"report_{report_type.value}_{date_suffix}.{extension}"
