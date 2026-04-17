/**
 * Main filter panel component with all filters
 */

import React, { useState } from "react";
import { useFilters } from "../hooks/useFilters";
import DateRangePicker from "./DateRangePicker";
import MultiSelect from "./MultiSelect";
import RangeSlider from "./RangeSlider";
import { TimePreset, ComplexityLevel } from "../context/types";

const TIME_PRESETS: TimePreset[] = ["1h", "24h", "7d", "30d"];
const COMPLEXITY_LEVELS: ComplexityLevel[] = ["SIMPLE", "MODERATE", "COMPLEX", "VERY_COMPLEX"];

interface FilterPanelProps {
  availableUsers?: string[];
  availableTools?: string[];
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  availableUsers = [],
  availableTools = [],
}) => {
  const filters = useFilters();
  const [isExpanded, setIsExpanded] = useState(false);

  const state = filters.state;
  const effectiveDateRange = filters.getEffectiveDateRange();

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 border-b border-gray-200"
      >
        <div className="flex items-center gap-3">
          <svg
            className="w-5 h-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          <span className="font-semibold text-gray-900">Filters</span>
          {filters.isFilterActive() && (
            <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-1 rounded">
              Active
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 transition-transform ${isExpanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </button>

      {/* Filter Content */}
      {isExpanded && (
        <div className="px-6 py-4 space-y-6 border-t border-gray-200">
          {/* Time Presets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <div className="grid grid-cols-4 gap-2">
              {TIME_PRESETS.map(preset => (
                <button
                  key={preset}
                  onClick={() => filters.setTimePreset(preset)}
                  className={`px-3 py-2 rounded text-sm font-medium transition ${
                    state.timePreset === preset
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {preset.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Date Range */}
          <DateRangePicker
            label="Custom Date Range"
            startDate={effectiveDateRange.startDate}
            endDate={effectiveDateRange.endDate}
            onChange={filters.setDateRange}
            onClear={() => filters.setTimePreset("24h")}
          />

          {/* Dimension Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableUsers.length > 0 && (
              <MultiSelect
                label="Users"
                placeholder="All users"
                options={availableUsers}
                selected={state.users}
                onChange={filters.setUsers}
              />
            )}

            {availableTools.length > 0 && (
              <MultiSelect
                label="Tools"
                placeholder="All tools"
                options={availableTools}
                selected={state.tools}
                onChange={filters.setTools}
              />
            )}

            <MultiSelect
              label="Complexity"
              placeholder="All complexities"
              options={COMPLEXITY_LEVELS}
              selected={state.complexities}
              onChange={filters.setComplexities}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={state.successStatus}
                onChange={e => filters.setSuccessStatus(e.target.value as any)}
                className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm"
              >
                <option value="all">All</option>
                <option value="success">Successful</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>

          {/* Range Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <RangeSlider
              label="Cost Range"
              unit="$"
              min={0}
              max={1000}
              step={10}
              value={state.costRange}
              onChange={filters.setCostRange}
            />

            <RangeSlider
              label="Latency Range"
              unit="ms"
              min={0}
              max={5000}
              step={100}
              value={state.latencyRange}
              onChange={filters.setLatencyRange}
            />
          </div>

          {/* Sorting */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={state.sortBy}
                onChange={e => filters.setSort(e.target.value, state.sortOrder)}
                className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm"
              >
                <option value="cost">Cost</option>
                <option value="latency">Latency</option>
                <option value="count">Count</option>
                <option value="effectiveness">Effectiveness</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Order
              </label>
              <select
                value={state.sortOrder}
                onChange={e => filters.setSort(state.sortBy, e.target.value as any)}
                className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={filters.resetAll}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Reset All
            </button>
            <button
              onClick={() => setIsExpanded(false)}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;
