/**
 * Analytics API client service
 */

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface QueryAnalyticsData {
  complexity_distribution: Record<string, number>;
  success_rate: number;
  avg_latency_by_complexity: Record<string, number>;
  total_cost: number;
  avg_cost_per_query: number;
}

export interface UserMetricsData {
  user_id: string;
  metrics: {
    query_count: number;
    total_cost: number;
    avg_cost: number;
  };
  spending_trend: Record<string, number>;
}

export interface AllUsersMetricsData {
  users: Record<string, { query_count: number; total_cost: number; avg_cost: number }>;
  total_users: number;
  top_users: Record<string, number>;
}

export interface ToolStatsData {
  tool_name: string;
  stats: {
    uses: number;
    successes: number;
    success_rate: number;
    avg_tokens: number;
    avg_duration_ms: number;
    avg_effectiveness: number;
  };
}

export interface AllToolsData {
  tools: Record<string, any>;
  total_tools: number;
  rankings: Record<string, number>;
}

export interface DailyCostsData {
  daily_costs: Record<string, number>;
  total_cost: number;
  avg_daily_cost: number;
}

export interface CostForecastData {
  days_ahead: number;
  forecast: number;
  daily_average: number;
}

export interface LatencyData {
  p50: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
  avg: number;
}

export interface StreamingSessionsData {
  total_sessions: number;
  completed_sessions: number;
  completion_rate: number;
  avg_duration_ms: number;
  avg_events: number;
  total_events: number;
}

export interface FilteredQuery {
  query: string;
  complexity: string;
  success: boolean;
  cost: number;
  duration_ms: number;
  timestamp: string;
}

export interface FilteredQueryResponse {
  queries: FilteredQuery[];
  total: number;
  limit: number;
  offset: number;
  filters: Record<string, any>;
}

export interface FilteredUserCost {
  user: string;
  cost: number;
}

export interface FilteredUserCostsResponse {
  users: FilteredUserCost[];
  total: number;
  limit: number;
  offset: number;
  filters: Record<string, any>;
}

class AnalyticsAPIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE) {
    this.baseURL = baseURL;
  }

  private async fetch<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(`${this.baseURL}${endpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Query Analytics
  async getQueryAnalytics(hours: number = 24): Promise<QueryAnalyticsData> {
    return this.fetch("/api/v1/analytics/queries", { hours });
  }

  async getQueryTrends(hours: number = 24): Promise<any> {
    return this.fetch("/api/v1/analytics/queries/trends", { hours });
  }

  // User Analytics
  async getAllUsersMetrics(hours: number = 24): Promise<AllUsersMetricsData> {
    return this.fetch("/api/v1/analytics/users", { hours });
  }

  async getUserMetrics(userId: string, hours: number = 24): Promise<UserMetricsData> {
    return this.fetch(`/api/v1/analytics/users/${userId}`, { hours });
  }

  // Tool Analytics
  async getAllToolsAnalytics(hours: number = 24): Promise<AllToolsData> {
    return this.fetch("/api/v1/analytics/tools", { hours });
  }

  async getToolAnalytics(toolName: string, hours: number = 24): Promise<ToolStatsData> {
    return this.fetch(`/api/v1/analytics/tools/${toolName}`, { hours });
  }

  // Cost Analytics
  async getDailyCosts(days: number = 30): Promise<DailyCostsData> {
    return this.fetch("/api/v1/analytics/costs/daily", { days });
  }

  async getForecastedCost(
    daysAhead: number = 7,
    lookbackDays: number = 30
  ): Promise<CostForecastData> {
    return this.fetch("/api/v1/analytics/costs/forecast", {
      days_ahead: daysAhead,
      lookback_days: lookbackDays,
    });
  }

  async getTopCostUsers(days: number = 30): Promise<{ top_users: Array<{ user: string; cost: number }> }> {
    return this.fetch("/api/v1/analytics/costs/by-user", { days });
  }

  // Performance Analytics
  async getLatencyMetrics(): Promise<LatencyData> {
    return this.fetch("/api/v1/analytics/performance/latency");
  }

  async getThroughputMetrics(): Promise<any> {
    return this.fetch("/api/v1/analytics/performance/throughput");
  }

  // Streaming Analytics
  async getStreamingSessionsAnalytics(hours: number = 24): Promise<StreamingSessionsData> {
    return this.fetch("/api/v1/analytics/streaming/sessions", { hours });
  }

  // Filtered Analytics (Phase 5)
  async getFilteredQueries(
    hours: number = 24,
    complexities?: string[],
    successStatus?: string,
    costMin?: number,
    costMax?: number,
    latencyMin?: number,
    latencyMax?: number,
    sortBy?: string,
    sortOrder?: string,
    limit?: number,
    offset?: number
  ): Promise<FilteredQueryResponse> {
    return this.fetch("/api/v1/analytics/queries/filtered", {
      hours,
      complexities: complexities?.join(","),
      success_status: successStatus,
      cost_min: costMin,
      cost_max: costMax,
      latency_min: latencyMin,
      latency_max: latencyMax,
      sort_by: sortBy,
      sort_order: sortOrder,
      limit,
      offset,
    });
  }

  async getFilteredUserCosts(
    days: number = 30,
    costMin?: number,
    costMax?: number,
    sortBy?: string,
    sortOrder?: string,
    limit?: number,
    offset?: number
  ): Promise<FilteredUserCostsResponse> {
    return this.fetch("/api/v1/analytics/costs/by-user/filtered", {
      days,
      cost_min: costMin,
      cost_max: costMax,
      sort_by: sortBy,
      sort_order: sortOrder,
      limit,
      offset,
    });
  }
}

export const analyticsAPI = new AnalyticsAPIClient();
export { AnalyticsAPIClient };
export default analyticsAPI;
