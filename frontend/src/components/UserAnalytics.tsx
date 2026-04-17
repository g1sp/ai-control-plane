/**
 * User Analytics component
 */

import React, { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from "recharts";
import { AllUsersData, UserMetrics } from "../types/analytics";

interface UserAnalyticsProps {
  data: AllUsersData;
}

export const UserAnalyticsComponent: React.FC<UserAnalyticsProps> = ({ data }) => {
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  // Convert top users to chart data
  const topUsersData = Object.entries(data.top_users)
    .map(([user, cost]) => ({ user, cost }))
    .slice(0, 10);

  // Sort users by spending for table
  const sortedUsers = Object.entries(data.users)
    .map(([userId, metrics]) => ({ userId, ...metrics }))
    .sort((a, b) => b.total_cost - a.total_cost);

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">User Analytics</h2>

        {/* Top Spenders Bar Chart */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Top 10 Spenders</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topUsersData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user" angle={-45} textAnchor="end" height={100} />
              <YAxis label={{ value: "Cost ($)", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Bar dataKey="cost" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Users Table */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">All Users ({data.total_users})</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">User</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Queries</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Total Cost</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Avg Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sortedUsers.map((user) => (
                  <tr key={user.userId} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">{user.userId}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{user.query_count}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">${user.total_cost.toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">${user.avg_cost.toFixed(4)}</td>
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

export default UserAnalyticsComponent;
