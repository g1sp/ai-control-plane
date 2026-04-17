/**
 * Tool Analytics component
 */

import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { AllToolsData } from "../types/analytics";

interface ToolAnalyticsProps {
  data: AllToolsData;
}

export const ToolAnalyticsComponent: React.FC<ToolAnalyticsProps> = ({ data }) => {
  // Prepare tool rankings for chart
  const rankingsData = Object.entries(data.rankings)
    .map(([tool, effectiveness]) => ({ tool, effectiveness }))
    .sort((a, b) => b.effectiveness - a.effectiveness);

  // Get detailed stats for top tools
  const topToolsStats = rankingsData.slice(0, 10).map((item) => {
    const stats = data.tools[item.tool];
    return {
      tool: item.tool,
      effectiveness: item.effectiveness,
      successRate: (stats.success_rate * 100).toFixed(1),
      uses: stats.uses,
      avgDuration: stats.avg_duration_ms.toFixed(0),
    };
  });

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Tool Analytics</h2>

        {/* Tool Rankings */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Tool Effectiveness Rankings</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rankingsData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="tool" />
              <Tooltip />
              <Bar dataKey="effectiveness" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tool Statistics Table */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Tool Statistics</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Tool</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Effectiveness</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Success Rate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Uses</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Avg Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {topToolsStats.map((stat) => (
                  <tr key={stat.tool} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{stat.tool}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-12 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{ width: `${stat.effectiveness * 100}%` }}
                          ></div>
                        </div>
                        <span className="ml-2 text-sm text-gray-600">{(stat.effectiveness * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{stat.successRate}%</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{stat.uses}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{stat.avgDuration}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolAnalyticsComponent;
