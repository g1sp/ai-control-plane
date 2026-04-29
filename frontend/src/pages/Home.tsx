import React, { useEffect, useState } from "react";
import { LatencyData } from "../services/analyticsAPI";
import MetricCard from "../components/MetricCard";
import HealthStatus from "../components/HealthStatus";
import QueryTimeline from "../components/QueryTimeline";
import CostTrend from "../components/CostTrend";
import ModelCostBreakdown from "../components/ModelCostBreakdown";

const DEMO_KEY = "pk-demo:sk-demo-secret-123";

interface HomeMetrics {
  todaysCost: number;
  queryCount: number;
  avgLatency: number;
  errorRate: number;
  loading: boolean;
  error: string | null;
}

const Home: React.FC = () => {
  const [metrics, setMetrics] = useState<HomeMetrics>({
    todaysCost: 0,
    queryCount: 0,
    avgLatency: 0,
    errorRate: 0,
    loading: true,
    error: null,
  });

  const fetchMetrics = async () => {
    try {
      const baseUrl = process.env.REACT_APP_API_BASE || "http://localhost:8000";

      const response = await fetch(`${baseUrl}/api/v1/analytics/queries?hours=24`, {
        headers: {
          "Authorization": `Bearer ${DEMO_KEY}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      const latencyResponse = await fetch(
        `${baseUrl}/api/v1/analytics/performance/latency`,
        {
          headers: {
            "Authorization": `Bearer ${DEMO_KEY}`,
          },
        }
      );

      const latencyData: LatencyData = await latencyResponse.json();

      const queryCount = Object.values(data.complexity_distribution as Record<string, number>).reduce(
        (a, b) => a + b,
        0
      ) as number;
      const errorRate = 1 - (data.success_rate || 0);

      setMetrics({
        todaysCost: data.total_cost || 0,
        queryCount: queryCount || 0,
        avgLatency: latencyData.avg || 0,
        errorRate: errorRate * 100,
        loading: false,
        error: null,
      });
    } catch (err) {
      setMetrics((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to fetch metrics",
      }));
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">AI Gateway</h1>
          <p className="text-slate-600">Home Network Monitor</p>
        </div>

        {/* Health Status */}
        <div className="mb-8">
          <HealthStatus demoKey={DEMO_KEY} />
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Today's Cost"
            value={`$${metrics.todaysCost.toFixed(3)}`}
            unit="USD"
            icon="💰"
            trend={metrics.loading ? "loading" : "stable"}
          />
          <MetricCard
            title="Queries"
            value={metrics.queryCount.toString()}
            unit="requests"
            icon="📊"
            trend={metrics.loading ? "loading" : "stable"}
          />
          <MetricCard
            title="Avg Latency"
            value={metrics.avgLatency.toFixed(0)}
            unit="ms"
            icon="⚡"
            trend={metrics.loading ? "loading" : "stable"}
          />
          <MetricCard
            title="Error Rate"
            value={metrics.errorRate.toFixed(1)}
            unit="%"
            icon="⚠️"
            trend={metrics.loading ? "loading" : "stable"}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <CostTrend demoKey={DEMO_KEY} />
          <ModelCostBreakdown demoKey={DEMO_KEY} />
        </div>

        {/* Recent Queries */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-4">Recent Queries (Last 24h)</h2>
          <QueryTimeline demoKey={DEMO_KEY} />
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Last updated: {new Date().toLocaleTimeString()}</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
