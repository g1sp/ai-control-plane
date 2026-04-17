/**
 * Main Dashboard page
 */

import React, { useState } from "react";
import {
  useQueryAnalytics,
  useAllUsersMetrics,
  useAllToolsAnalytics,
  useDailyCosts,
  useLatencyMetrics,
  useStreamingSessionsAnalytics,
} from "../hooks/useAnalytics";
import MetricCard from "../components/MetricCard";
import QueryAnalytics from "../components/QueryAnalytics";
import UserAnalytics from "../components/UserAnalytics";
import ToolAnalytics from "../components/ToolAnalytics";
import CostAnalytics from "../components/CostAnalytics";
import PerformanceAnalytics from "../components/PerformanceAnalytics";
import StreamingAnalytics from "../components/StreamingAnalytics";
import ReportGenerator from "../components/ReportGenerator";
import { TimeRange } from "../types/analytics";

export const Dashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [tab, setTab] = useState<"overview" | "queries" | "users" | "tools" | "costs" | "performance" | "streaming" | "reports">(
    "overview"
  );

  // Convert time range to hours
  const hours = timeRange === "1h" ? 1 : timeRange === "24h" ? 24 : timeRange === "7d" ? 168 : 720;

  // Fetch analytics data
  const query = useQueryAnalytics(hours);
  const users = useAllUsersMetrics(hours);
  const tools = useAllToolsAnalytics(hours);
  const costs = useDailyCosts(30);
  const latency = useLatencyMetrics();
  const streaming = useStreamingSessionsAnalytics(hours);

  const isLoading = query.loading || users.loading || tools.loading || costs.loading || latency.loading || streaming.loading;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
              <p className="text-gray-600 mt-1">Monitor your AI gateway performance and usage</p>
            </div>

            {/* Time Range Selector */}
            <div className="flex gap-2">
              {(["1h", "24h", "7d", "30d"] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-2 rounded text-sm font-medium transition ${
                    timeRange === range
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  {range.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex gap-8" aria-label="Tabs">
            {(["overview", "queries", "users", "tools", "costs", "performance", "streaming", "reports"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-4 font-medium text-sm border-b-2 transition ${
                  tab === t
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Overview Tab */}
            {tab === "overview" && (
              <div className="space-y-8">
                {/* Key Metrics */}
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Key Metrics</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricCard
                      title="Success Rate"
                      value={`${(query.data?.success_rate * 100).toFixed(1)}%`}
                      color="green"
                    />
                    <MetricCard
                      title="Total Cost"
                      value={`$${query.data?.total_cost.toFixed(2)}`}
                      color="blue"
                    />
                    <MetricCard
                      title="Avg Cost/Query"
                      value={`$${query.data?.avg_cost_per_query.toFixed(4)}`}
                      color="yellow"
                    />
                    <MetricCard
                      title="Active Users"
                      value={users.data?.total_users || 0}
                      color="purple"
                    />
                  </div>
                </div>

                {/* Complexity Distribution */}
                {query.data && <QueryAnalytics data={query.data} />}

                {/* Cost Trends */}
                {costs.data && <CostAnalytics data={costs.data} />}

                {/* Performance */}
                {latency.data && <PerformanceAnalytics latencyData={latency.data} />}
              </div>
            )}

            {/* Query Analytics Tab */}
            {tab === "queries" && query.data && <QueryAnalytics data={query.data} />}

            {/* User Analytics Tab */}
            {tab === "users" && users.data && <UserAnalytics data={users.data} />}

            {/* Tool Analytics Tab */}
            {tab === "tools" && tools.data && <ToolAnalytics data={tools.data} />}

            {/* Cost Analytics Tab */}
            {tab === "costs" && costs.data && <CostAnalytics data={costs.data} />}

            {/* Performance Tab */}
            {tab === "performance" && latency.data && (
              <PerformanceAnalytics latencyData={latency.data} />
            )}

            {/* Streaming Tab */}
            {tab === "streaming" && streaming.data && <StreamingAnalytics data={streaming.data} />}

            {/* Reports Tab */}
            {tab === "reports" && <ReportGenerator />}
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
