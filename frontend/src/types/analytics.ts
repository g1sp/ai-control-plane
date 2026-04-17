/**
 * TypeScript types for analytics data
 */

export type ComplexityLevel = "SIMPLE" | "MODERATE" | "COMPLEX" | "VERY_COMPLEX";

export interface QueryAnalytics {
  complexity_distribution: Record<ComplexityLevel, number>;
  success_rate: number;
  avg_latency_by_complexity: Record<ComplexityLevel, number>;
  total_cost: number;
  avg_cost_per_query: number;
}

export interface UserMetrics {
  query_count: number;
  total_cost: number;
  avg_cost: number;
}

export interface UserMetricsData {
  user_id: string;
  metrics: UserMetrics;
  spending_trend: Record<string, number>;
}

export interface AllUsersData {
  users: Record<string, UserMetrics>;
  total_users: number;
  top_users: Record<string, number>;
}

export interface ToolStats {
  uses: number;
  successes: number;
  success_rate: number;
  avg_tokens: number;
  avg_duration_ms: number;
  avg_effectiveness: number;
}

export interface ToolAnalyticsData {
  tool_name: string;
  stats: ToolStats;
}

export interface AllToolsData {
  tools: Record<string, ToolStats>;
  total_tools: number;
  rankings: Record<string, number>;
}

export interface CostData {
  daily_costs: Record<string, number>;
  total_cost: number;
  avg_daily_cost: number;
}

export interface CostForecastData {
  days_ahead: number;
  forecast: number;
  daily_average: number;
}

export interface TopCostUser {
  user: string;
  cost: number;
}

export interface LatencyPercentiles {
  p50: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
  avg: number;
}

export interface StreamingSessionStats {
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
  avg_duration_ms: number;
  avg_events: number;
  total_events: number;
}

export interface ThroughputData {
  throughput_samples: Record<string, number>;
  avg_throughput: number;
}

export type TimeRange = "1h" | "24h" | "7d" | "30d";
