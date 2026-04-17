/**
 * Streaming Analytics component
 */

import React from "react";
import { StreamingSessionStats } from "../types/analytics";

interface StreamingAnalyticsProps {
  data: StreamingSessionStats;
}

export const StreamingAnalyticsComponent: React.FC<StreamingAnalyticsProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6">Streaming Session Analytics</h2>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Total Sessions</p>
            <p className="text-3xl font-bold text-blue-600">{data.total_sessions}</p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Completion Rate</p>
            <p className="text-3xl font-bold text-green-600">{(data.completion_rate * 100).toFixed(1)}%</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Completed Sessions</p>
            <p className="text-3xl font-bold text-purple-600">{data.completed_sessions}</p>
          </div>

          <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Avg Duration</p>
            <p className="text-3xl font-bold text-yellow-600">{(data.avg_duration_ms / 1000).toFixed(1)}s</p>
          </div>

          <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Avg Events/Session</p>
            <p className="text-3xl font-bold text-red-600">{data.avg_events.toFixed(0)}</p>
          </div>

          <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Total Events</p>
            <p className="text-3xl font-bold text-pink-600">{data.total_events}</p>
          </div>
        </div>

        {/* Detailed Summary */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Summary</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <p>
              <span className="font-medium text-gray-900">Sessions completed:</span> {data.completed_sessions} out of{" "}
              {data.total_sessions} ({(data.completion_rate * 100).toFixed(1)}% completion rate)
            </p>
            <p>
              <span className="font-medium text-gray-900">Average session duration:</span> {(data.avg_duration_ms / 1000).toFixed(1)} seconds
            </p>
            <p>
              <span className="font-medium text-gray-900">Total events generated:</span> {data.total_events} events across all sessions
            </p>
            <p>
              <span className="font-medium text-gray-900">Average events per session:</span> {data.avg_events.toFixed(1)} events
            </p>
            <p>
              <span className="font-medium text-gray-900">Abandonment rate:</span> {((1 - data.completion_rate) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamingAnalyticsComponent;
