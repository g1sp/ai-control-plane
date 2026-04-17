/**
 * Query Analytics component with Recharts
 */

import React from "react";
import { PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";
import { QueryAnalytics } from "../types/analytics";

interface QueryAnalyticsProps {
  data: QueryAnalytics;
}

const COLORS = {
  SIMPLE: "#10b981",
  MODERATE: "#f59e0b",
  COMPLEX: "#ef4444",
  VERY_COMPLEX: "#8b5cf6",
};

export const QueryAnalyticsComponent: React.FC<QueryAnalyticsProps> = ({ data }) => {
  // Prepare complexity distribution for pie chart
  const complexityData = Object.entries(data.complexity_distribution).map(([key, value]) => ({
    name: key,
    value,
    color: COLORS[key as keyof typeof COLORS],
  }));

  // Prepare latency data for bar chart
  const latencyData = Object.entries(data.avg_latency_by_complexity).map(([complexity, latency]) => ({
    complexity,
    latency,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Query Analytics</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Complexity Distribution Pie Chart */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Query Complexity Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={complexityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {complexityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Average Latency by Complexity Bar Chart */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Average Latency by Complexity</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="complexity" />
                <YAxis label={{ value: "Latency (ms)", angle: -90, position: "insideLeft" }} />
                <Tooltip />
                <Bar dataKey="latency" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-3xl font-bold text-green-600">{(data.success_rate * 100).toFixed(1)}%</p>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <p className="text-sm text-gray-600">Total Cost</p>
            <p className="text-3xl font-bold text-blue-600">${data.total_cost.toFixed(2)}</p>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <p className="text-sm text-gray-600">Avg Cost/Query</p>
            <p className="text-3xl font-bold text-purple-600">${data.avg_cost_per_query.toFixed(4)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryAnalyticsComponent;
