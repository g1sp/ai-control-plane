"""Analytics service for computing aggregated metrics and trends."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict


class TimeWindow(str, Enum):
    """Time window for analytics."""
    ONE_HOUR = "1h"
    ONE_DAY = "24h"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"


class QueryAnalytics:
    """Analyze query patterns and complexity."""

    def __init__(self):
        """Initialize query analytics."""
        self.queries: List[Dict] = []

    def add_query(self, query: str, complexity: str, success: bool, cost: float, duration_ms: int) -> None:
        """Record a query for analytics."""
        self.queries.append({
            "query": query,
            "complexity": complexity,
            "success": success,
            "cost": cost,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow()
        })

    def get_complexity_distribution(self, hours: int = 24) -> Dict[str, int]:
        """Get distribution of query complexity levels."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [q for q in self.queries if q["timestamp"] > cutoff]

        distribution = defaultdict(int)
        for q in recent:
            distribution[q["complexity"]] += 1

        return dict(distribution)

    def get_success_rate(self, hours: int = 24) -> float:
        """Get query success rate."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [q for q in self.queries if q["timestamp"] > cutoff]

        if not recent:
            return 1.0

        successes = sum(1 for q in recent if q["success"])
        return successes / len(recent)

    def get_avg_latency_by_complexity(self, hours: int = 24) -> Dict[str, float]:
        """Get average latency grouped by complexity."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [q for q in self.queries if q["timestamp"] > cutoff]

        by_complexity = defaultdict(list)
        for q in recent:
            by_complexity[q["complexity"]].append(q["duration_ms"])

        result = {}
        for complexity, durations in by_complexity.items():
            result[complexity] = sum(durations) / len(durations)

        return result

    def get_total_cost(self, hours: int = 24) -> float:
        """Get total query cost."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [q for q in self.queries if q["timestamp"] > cutoff]
        return sum(q["cost"] for q in recent)

    def get_avg_cost_per_query(self, hours: int = 24) -> float:
        """Get average cost per query."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [q for q in self.queries if q["timestamp"] > cutoff]

        if not recent:
            return 0.0

        return sum(q["cost"] for q in recent) / len(recent)

    def filter_queries(
        self,
        hours: int = 24,
        complexities: Optional[List[str]] = None,
        success_status: str = "all",
        cost_min: Optional[float] = None,
        cost_max: Optional[float] = None,
        latency_min: Optional[int] = None,
        latency_max: Optional[int] = None,
        sort_by: str = "cost",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """Filter queries with multiple dimensions and return paginated results."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        results = [q for q in self.queries if q["timestamp"] > cutoff]

        # Filter by complexity
        if complexities:
            results = [q for q in results if q["complexity"] in complexities]

        # Filter by success status
        if success_status == "success":
            results = [q for q in results if q["success"]]
        elif success_status == "failed":
            results = [q for q in results if not q["success"]]

        # Filter by cost range
        if cost_min is not None:
            results = [q for q in results if q["cost"] >= cost_min]
        if cost_max is not None:
            results = [q for q in results if q["cost"] <= cost_max]

        # Filter by latency range
        if latency_min is not None:
            results = [q for q in results if q["duration_ms"] >= latency_min]
        if latency_max is not None:
            results = [q for q in results if q["duration_ms"] <= latency_max]

        # Sort
        reverse = sort_order == "desc"
        if sort_by == "cost":
            results.sort(key=lambda x: x["cost"], reverse=reverse)
        elif sort_by == "latency":
            results.sort(key=lambda x: x["duration_ms"], reverse=reverse)
        elif sort_by == "count":
            results.sort(key=lambda x: x.get("query_count", 1), reverse=reverse)

        # Paginate
        total = len(results)
        paginated = results[offset : offset + limit]

        return paginated, total


class UserAnalytics:
    """Analyze per-user metrics and spending."""

    def __init__(self):
        """Initialize user analytics."""
        self.user_queries: Dict[str, List[Dict]] = defaultdict(list)

    def add_user_query(self, user_id: str, query_count: int, cost: float, tool_used: str) -> None:
        """Record user query activity."""
        self.user_queries[user_id].append({
            "query_count": query_count,
            "cost": cost,
            "tool_used": tool_used,
            "timestamp": datetime.utcnow()
        })

    def get_all_users_metrics(self, hours: int = 24) -> Dict[str, Dict[str, float]]:
        """Get metrics for all users."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = {}

        for user_id, queries in self.user_queries.items():
            recent = [q for q in queries if q["timestamp"] > cutoff]

            if recent:
                result[user_id] = {
                    "query_count": sum(q["query_count"] for q in recent),
                    "total_cost": sum(q["cost"] for q in recent),
                    "avg_cost": sum(q["cost"] for q in recent) / len(recent),
                }

        return result

    def get_user_metrics(self, user_id: str, hours: int = 24) -> Dict[str, float]:
        """Get metrics for specific user."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        queries = self.user_queries.get(user_id, [])
        recent = [q for q in queries if q["timestamp"] > cutoff]

        if not recent:
            return {
                "query_count": 0,
                "total_cost": 0.0,
                "avg_cost": 0.0,
            }

        return {
            "query_count": sum(q["query_count"] for q in recent),
            "total_cost": sum(q["cost"] for q in recent),
            "avg_cost": sum(q["cost"] for q in recent) / len(recent),
        }

    def get_user_spending_trend(self, user_id: str, days: int = 7) -> Dict[str, float]:
        """Get daily spending trend for user."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        queries = self.user_queries.get(user_id, [])
        recent = [q for q in queries if q["timestamp"] > cutoff]

        by_date = defaultdict(float)
        for q in recent:
            date_key = q["timestamp"].strftime("%Y-%m-%d")
            by_date[date_key] += q["cost"]

        return dict(by_date)

    def get_top_users_by_spending(self, hours: int = 24, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top spending users."""
        metrics = self.get_all_users_metrics(hours)
        sorted_users = sorted(metrics.items(), key=lambda x: x[1]["total_cost"], reverse=True)
        return [(user, data["total_cost"]) for user, data in sorted_users[:limit]]


class ToolAnalytics:
    """Analyze tool usage and effectiveness."""

    def __init__(self):
        """Initialize tool analytics."""
        self.tool_usage: Dict[str, List[Dict]] = defaultdict(list)

    def add_tool_use(self, tool_name: str, success: bool, tokens: int, duration_ms: int, effectiveness: float) -> None:
        """Record tool usage."""
        self.tool_usage[tool_name].append({
            "success": success,
            "tokens": tokens,
            "duration_ms": duration_ms,
            "effectiveness": effectiveness,
            "timestamp": datetime.utcnow()
        })

    def get_all_tools_stats(self, hours: int = 24) -> Dict[str, Dict[str, float]]:
        """Get statistics for all tools."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = {}

        for tool_name, uses in self.tool_usage.items():
            recent = [u for u in uses if u["timestamp"] > cutoff]

            if recent:
                successes = sum(1 for u in recent if u["success"])
                result[tool_name] = {
                    "uses": len(recent),
                    "successes": successes,
                    "success_rate": successes / len(recent),
                    "avg_tokens": sum(u["tokens"] for u in recent) / len(recent),
                    "avg_duration_ms": sum(u["duration_ms"] for u in recent) / len(recent),
                    "avg_effectiveness": sum(u["effectiveness"] for u in recent) / len(recent),
                }

        return result

    def get_tool_stats(self, tool_name: str, hours: int = 24) -> Dict[str, float]:
        """Get statistics for specific tool."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        uses = self.tool_usage.get(tool_name, [])
        recent = [u for u in uses if u["timestamp"] > cutoff]

        if not recent:
            return {
                "uses": 0,
                "success_rate": 0.0,
                "avg_tokens": 0.0,
                "avg_duration_ms": 0.0,
                "avg_effectiveness": 0.0,
            }

        successes = sum(1 for u in recent if u["success"])
        return {
            "uses": len(recent),
            "successes": successes,
            "success_rate": successes / len(recent),
            "avg_tokens": sum(u["tokens"] for u in recent) / len(recent),
            "avg_duration_ms": sum(u["duration_ms"] for u in recent) / len(recent),
            "avg_effectiveness": sum(u["effectiveness"] for u in recent) / len(recent),
        }

    def get_tool_rankings(self, hours: int = 24) -> List[Tuple[str, float]]:
        """Get tools ranked by effectiveness."""
        stats = self.get_all_tools_stats(hours)
        ranked = sorted(stats.items(), key=lambda x: x[1]["avg_effectiveness"], reverse=True)
        return [(tool, data["avg_effectiveness"]) for tool, data in ranked]


class CostAnalytics:
    """Analyze cost patterns and trends."""

    def __init__(self):
        """Initialize cost analytics."""
        self.daily_costs: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def add_cost(self, date: str, user_id: str, cost: float) -> None:
        """Record cost for date and user."""
        self.daily_costs[date][user_id] += cost

    def get_daily_costs(self, days: int = 30) -> Dict[str, float]:
        """Get daily cost breakdown."""
        dates = sorted(self.daily_costs.keys())[-days:]
        result = {}

        for date in dates:
            result[date] = sum(self.daily_costs[date].values())

        return result

    def get_total_cost(self, days: int = 30) -> float:
        """Get total cost for period."""
        daily = self.get_daily_costs(days)
        return sum(daily.values())

    def get_avg_daily_cost(self, days: int = 30) -> float:
        """Get average daily cost."""
        daily = self.get_daily_costs(days)

        if not daily:
            return 0.0

        return sum(daily.values()) / len(daily)

    def forecast_cost(self, days_ahead: int = 7, lookback_days: int = 30) -> float:
        """Forecast cost for coming days (simple average)."""
        avg_daily = self.get_avg_daily_cost(lookback_days)
        return avg_daily * days_ahead

    def get_cost_by_user(self, date: str) -> Dict[str, float]:
        """Get cost breakdown by user for date."""
        return dict(self.daily_costs.get(date, {}))

    def get_top_cost_users(self, days: int = 30, limit: int = 10) -> List[Tuple[str, float]]:
        """Get top spenders."""
        user_totals = defaultdict(float)

        for date_costs in list(self.daily_costs.values())[-days:]:
            for user_id, cost in date_costs.items():
                user_totals[user_id] += cost

        sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]

    def filter_users_by_cost(
        self,
        days: int = 30,
        cost_min: Optional[float] = None,
        cost_max: Optional[float] = None,
        sort_by: str = "cost",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, float]], int]:
        """Filter users by cost with pagination."""
        user_totals = defaultdict(float)

        for date_costs in list(self.daily_costs.values())[-days:]:
            for user_id, cost in date_costs.items():
                user_totals[user_id] += cost

        # Filter by cost range
        results = list(user_totals.items())
        if cost_min is not None:
            results = [(u, c) for u, c in results if c >= cost_min]
        if cost_max is not None:
            results = [(u, c) for u, c in results if c <= cost_max]

        # Sort
        reverse = sort_order == "desc"
        if sort_by == "cost":
            results.sort(key=lambda x: x[1], reverse=reverse)
        else:
            results.sort(key=lambda x: x[0], reverse=reverse)

        # Return paginated results
        total = len(results)
        paginated = results[offset : offset + limit]
        return [{"user": u, "cost": c} for u, c in paginated], total


class PerformanceAnalytics:
    """Analyze system performance metrics."""

    def __init__(self):
        """Initialize performance analytics."""
        self.latencies: List[int] = []
        self.throughput_samples: Dict[str, int] = defaultdict(int)

    def add_latency(self, latency_ms: int) -> None:
        """Record latency measurement."""
        self.latencies.append(latency_ms)

    def add_throughput_sample(self, timestamp: str, count: int) -> None:
        """Record throughput sample."""
        self.throughput_samples[timestamp] = count

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Get latency percentiles (p50, p95, p99)."""
        if not self.latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        return {
            "p50": sorted_latencies[int(n * 0.50)],
            "p95": sorted_latencies[int(n * 0.95)],
            "p99": sorted_latencies[int(n * 0.99)],
            "min": float(min(sorted_latencies)),
            "max": float(max(sorted_latencies)),
            "avg": sum(sorted_latencies) / n,
        }

    def get_avg_latency(self) -> float:
        """Get average latency."""
        if not self.latencies:
            return 0.0

        return sum(self.latencies) / len(self.latencies)

    def get_throughput(self) -> Dict[str, int]:
        """Get throughput samples."""
        return dict(self.throughput_samples)

    def get_avg_throughput(self) -> float:
        """Get average requests per second."""
        if not self.throughput_samples:
            return 0.0

        return sum(self.throughput_samples.values()) / len(self.throughput_samples)


class StreamingAnalytics:
    """Analyze streaming session patterns."""

    def __init__(self):
        """Initialize streaming analytics."""
        self.sessions: List[Dict] = []

    def add_session(self, session_id: str, completed: bool, duration_ms: int, event_count: int) -> None:
        """Record streaming session."""
        self.sessions.append({
            "session_id": session_id,
            "completed": completed,
            "duration_ms": duration_ms,
            "event_count": event_count,
            "timestamp": datetime.utcnow()
        })

    def get_session_completion_rate(self, hours: int = 24) -> float:
        """Get session completion rate."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [s for s in self.sessions if s["timestamp"] > cutoff]

        if not recent:
            return 1.0

        completed = sum(1 for s in recent if s["completed"])
        return completed / len(recent)

    def get_avg_session_duration(self, hours: int = 24) -> float:
        """Get average session duration."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [s for s in self.sessions if s["timestamp"] > cutoff]

        if not recent:
            return 0.0

        return sum(s["duration_ms"] for s in recent) / len(recent)

    def get_avg_events_per_session(self, hours: int = 24) -> float:
        """Get average events per session."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [s for s in self.sessions if s["timestamp"] > cutoff]

        if not recent:
            return 0.0

        return sum(s["event_count"] for s in recent) / len(recent)

    def get_session_stats(self, hours: int = 24) -> Dict[str, float]:
        """Get comprehensive session statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [s for s in self.sessions if s["timestamp"] > cutoff]

        if not recent:
            return {
                "total_sessions": 0,
                "completion_rate": 0.0,
                "avg_duration_ms": 0.0,
                "avg_events": 0.0,
                "total_events": 0,
            }

        completed = sum(1 for s in recent if s["completed"])

        return {
            "total_sessions": len(recent),
            "completed_sessions": completed,
            "completion_rate": completed / len(recent),
            "avg_duration_ms": sum(s["duration_ms"] for s in recent) / len(recent),
            "avg_events": sum(s["event_count"] for s in recent) / len(recent),
            "total_events": sum(s["event_count"] for s in recent),
        }


# Global analytics instances
_analytics_store = {
    "queries": QueryAnalytics(),
    "users": UserAnalytics(),
    "tools": ToolAnalytics(),
    "costs": CostAnalytics(),
    "performance": PerformanceAnalytics(),
    "streaming": StreamingAnalytics(),
}


def get_query_analytics() -> QueryAnalytics:
    """Get global query analytics instance."""
    return _analytics_store["queries"]


def get_user_analytics() -> UserAnalytics:
    """Get global user analytics instance."""
    return _analytics_store["users"]


def get_tool_analytics() -> ToolAnalytics:
    """Get global tool analytics instance."""
    return _analytics_store["tools"]


def get_cost_analytics() -> CostAnalytics:
    """Get global cost analytics instance."""
    return _analytics_store["costs"]


def get_performance_analytics() -> PerformanceAnalytics:
    """Get global performance analytics instance."""
    return _analytics_store["performance"]


def get_streaming_analytics() -> StreamingAnalytics:
    """Get global streaming analytics instance."""
    return _analytics_store["streaming"]
