/**
 * Cost Analytics component
 */

import React from "react";
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { CostData } from "../types/analytics";

interface CostAnalyticsProps {
  data: CostData;
}

export const CostAnalyticsComponent: React.FC<CostAnalyticsProps> = ({ data }) => {
  // Prepare daily costs for chart
  const chartData = Object.entries(data.daily_costs)
    .map(([date, cost]) => ({ date, cost }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Cost Analytics</h2>

        {/* Daily Cost Trend */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Daily Cost Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis label={{ value: "Cost ($)", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Area type="monotone" dataKey="cost" fill="#3b82f6" stroke="#1e40af" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Cost Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Total Cost</p>
            <p className="text-3xl font-bold text-blue-600">${data.total_cost.toFixed(2)}</p>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Daily Average</p>
            <p className="text-3xl font-bold text-purple-600">${data.avg_daily_cost.toFixed(2)}</p>
          </div>
          <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Days Tracked</p>
            <p className="text-3xl font-bold text-yellow-600">{Object.keys(data.daily_costs).length}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostAnalyticsComponent;
