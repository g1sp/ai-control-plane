/**
 * Performance Analytics component
 */

import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { LatencyPercentiles } from "../types/analytics";

interface PerformanceAnalyticsProps {
  latencyData: LatencyPercentiles;
}

export const PerformanceAnalyticsComponent: React.FC<PerformanceAnalyticsProps> = ({ latencyData }) => {
  // Prepare latency percentiles for chart
  const chartData = [
    { percentile: "Min", latency: latencyData.min },
    { percentile: "Avg", latency: latencyData.avg },
    { percentile: "P50", latency: latencyData.p50 },
    { percentile: "P95", latency: latencyData.p95 },
    { percentile: "P99", latency: latencyData.p99 },
    { percentile: "Max", latency: latencyData.max },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Performance Analytics</h2>

        {/* Latency Percentiles Chart */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Latency Distribution (ms)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="percentile" />
              <YAxis label={{ value: "Latency (ms)", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Bar dataKey="latency" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Latency Statistics */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Latency Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Min</p>
              <p className="text-2xl font-bold text-blue-600">{latencyData.min.toFixed(0)}ms</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Avg</p>
              <p className="text-2xl font-bold text-green-600">{latencyData.avg.toFixed(0)}ms</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">P50</p>
              <p className="text-2xl font-bold text-yellow-600">{latencyData.p50.toFixed(0)}ms</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">P95</p>
              <p className="text-2xl font-bold text-orange-600">{latencyData.p95.toFixed(0)}ms</p>
            </div>
            <div className="bg-red-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">P99</p>
              <p className="text-2xl font-bold text-red-600">{latencyData.p99.toFixed(0)}ms</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-600">Max</p>
              <p className="text-2xl font-bold text-purple-600">{latencyData.max.toFixed(0)}ms</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceAnalyticsComponent;
