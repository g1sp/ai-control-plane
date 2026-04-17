/**
 * User Analytics component
 */

import React, { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from "recharts";
import { AllUsersData, UserMetrics } from "../types/analytics";
import { useFilteredUserCosts } from "../hooks/useFilteredAnalytics";
import { useFilters } from "../hooks/useFilters";

interface UserAnalyticsProps {
  data: AllUsersData;
}

export const UserAnalyticsComponent: React.FC<UserAnalyticsProps> = ({ data }) => {
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState<"user" | "queries" | "cost">("cost");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const filters = useFilters();
  const filteredCosts = useFilteredUserCosts(pageSize);

  // Convert top users to chart data
  const topUsersData = Object.entries(data.top_users)
    .map(([user, cost]) => ({ user, cost }))
    .slice(0, 10);

  // Sort users by spending for table
  let sortedUsers = Object.entries(data.users)
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
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">
              All Users ({filteredCosts.data?.total || data.total_users})
            </h3>
            {filteredCosts.data && filteredCosts.data.total > pageSize && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  ← Prev
                </button>
                <span className="text-sm text-gray-600">
                  Page {page + 1} of {Math.ceil(filteredCosts.data.total / pageSize)}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={(page + 1) * pageSize >= (filteredCosts.data?.total || 0)}
                  className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
                >
                  Next →
                </button>
              </div>
            )}
          </div>

          {filteredCosts.loading ? (
            <div className="text-center py-4">Loading filtered data...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase cursor-pointer hover:bg-gray-100"
                      onClick={() => setSortColumn("user")}>
                      User {sortColumn === "user" && "▼"}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase cursor-pointer hover:bg-gray-100"
                      onClick={() => setSortColumn("queries")}>
                      Queries {sortColumn === "queries" && "▼"}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase cursor-pointer hover:bg-gray-100"
                      onClick={() => setSortColumn("cost")}>
                      Total Cost {sortColumn === "cost" && "▼"}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Avg Cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredCosts.data?.users?.map((user) => (
                    <tr key={user.user} className="hover:bg-gray-50 cursor-pointer">
                      <td className="px-6 py-4 text-sm text-gray-900 font-medium">{user.user}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">—</td>
                      <td className="px-6 py-4 text-sm text-gray-600">${user.cost.toFixed(2)}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">—</td>
                    </tr>
                  )) || sortedUsers.map((user) => (
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
          )}
        </div>
      </div>
    </div>
  );
};

export default UserAnalyticsComponent;
