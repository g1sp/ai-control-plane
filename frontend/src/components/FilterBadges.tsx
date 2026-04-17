/**
 * Filter badges showing active filters with clear buttons
 */

import React from "react";
import { useFilters } from "../hooks/useFilters";

export const FilterBadges: React.FC = () => {
  const filters = useFilters();

  if (!filters.isFilterActive()) {
    return null;
  }

  const badges = [];

  // Time filter
  if (filters.state.dateRange) {
    badges.push(
      <badge key="date">
        📅 {filters.state.dateRange.startDate} to {filters.state.dateRange.endDate}
      </badge>
    );
  } else if (filters.state.timePreset && filters.state.timePreset !== "24h") {
    badges.push(
      <badge key="time">
        ⏱️ {filters.state.timePreset.toUpperCase()}
      </badge>
    );
  }

  // Users filter
  if (filters.state.users) {
    badges.push(
      <badge key="users">
        👤 Users: {filters.state.users.length}
      </badge>
    );
  }

  // Tools filter
  if (filters.state.tools) {
    badges.push(
      <badge key="tools">
        🔧 Tools: {filters.state.tools.length}
      </badge>
    );
  }

  // Complexity filter
  if (filters.state.complexities) {
    badges.push(
      <badge key="complexity">
        📊 Complexity: {filters.state.complexities.length}
      </badge>
    );
  }

  // Status filter
  if (filters.state.successStatus !== "all") {
    badges.push(
      <badge key="status">
        ✓ {filters.state.successStatus === "success" ? "Success" : "Failed"}
      </badge>
    );
  }

  // Cost range filter
  if (filters.state.costRange) {
    badges.push(
      <badge key="cost">
        💵 ${filters.state.costRange[0]} - ${filters.state.costRange[1]}
      </badge>
    );
  }

  // Latency range filter
  if (filters.state.latencyRange) {
    badges.push(
      <badge key="latency">
        ⚡ {filters.state.latencyRange[0]} - {filters.state.latencyRange[1]}ms
      </badge>
    );
  }

  if (badges.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {badges.map((badge, index) => (
        <div
          key={index}
          className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
        >
          {badge}
          <button
            onClick={filters.resetAll}
            className="ml-1 hover:text-blue-600"
            title="Clear filters"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};

export default FilterBadges;
