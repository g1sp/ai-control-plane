/**
 * Filter Context for managing analytics filters globally
 */

import React, { createContext, useReducer, useCallback, useMemo, useEffect } from "react";
import {
  FilterState,
  FilterAction,
  FilterContextType,
  defaultFilterState,
  DateRange,
  TimePreset,
  ComplexityLevel,
  SuccessStatus,
  SortOrder,
} from "./types";

export const FilterContext = createContext<FilterContextType | undefined>(undefined);

// Calculate days ago helper
function getDaysAgo(days: number): DateRange {
  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - days);

  return {
    startDate: start.toISOString().split("T")[0],
    endDate: end.toISOString().split("T")[0],
  };
}

// Get date range from time preset
function getDateRangeFromPreset(preset: TimePreset | null): DateRange {
  if (!preset) {
    return getDaysAgo(1);
  }

  switch (preset) {
    case "1h":
      // For 1 hour, use today's date (backend will filter by hours)
      return getDaysAgo(0);
    case "24h":
      return getDaysAgo(1);
    case "7d":
      return getDaysAgo(7);
    case "30d":
      return getDaysAgo(30);
    default:
      return getDaysAgo(1);
  }
}

// Filter reducer
function filterReducer(state: FilterState, action: FilterAction): FilterState {
  switch (action.type) {
    case "SET_DATE_RANGE":
      return {
        ...state,
        dateRange: action.payload,
        timePreset: null,  // Clear preset when using custom range
      };

    case "SET_TIME_PRESET":
      return {
        ...state,
        timePreset: action.payload,
        dateRange: null,  // Clear custom range when using preset
      };

    case "SET_USERS":
      return { ...state, users: action.payload };

    case "SET_TOOLS":
      return { ...state, tools: action.payload };

    case "SET_COMPLEXITIES":
      return { ...state, complexities: action.payload };

    case "SET_SUCCESS_STATUS":
      return { ...state, successStatus: action.payload };

    case "SET_COST_RANGE":
      return { ...state, costRange: action.payload };

    case "SET_LATENCY_RANGE":
      return { ...state, latencyRange: action.payload };

    case "SET_SORT":
      return {
        ...state,
        sortBy: action.payload.field,
        sortOrder: action.payload.order,
      };

    case "RESET_ALL":
      return defaultFilterState;

    case "LOAD_FROM_URL":
      return action.payload;

    default:
      return state;
  }
}

// Parse URL query parameters into filter state
function parseUrlToFilters(search: string): Partial<FilterState> {
  const params = new URLSearchParams(search);
  const filters: Partial<FilterState> = {};

  // Date range
  const startDate = params.get("startDate");
  const endDate = params.get("endDate");
  if (startDate && endDate) {
    filters.dateRange = { startDate, endDate };
    filters.timePreset = null;
  }

  // Time preset
  const timePreset = params.get("timePreset") as TimePreset | null;
  if (timePreset && !filters.dateRange) {
    filters.timePreset = timePreset;
  }

  // Users
  const users = params.get("users");
  if (users) {
    filters.users = users.split(",");
  }

  // Tools
  const tools = params.get("tools");
  if (tools) {
    filters.tools = tools.split(",");
  }

  // Complexities
  const complexities = params.get("complexities");
  if (complexities) {
    filters.complexities = complexities.split(",") as ComplexityLevel[];
  }

  // Success status
  const successStatus = params.get("successStatus") as SuccessStatus | null;
  if (successStatus) {
    filters.successStatus = successStatus;
  }

  // Cost range
  const costMin = params.get("costMin");
  const costMax = params.get("costMax");
  if (costMin && costMax) {
    filters.costRange = [parseFloat(costMin), parseFloat(costMax)];
  }

  // Latency range
  const latencyMin = params.get("latencyMin");
  const latencyMax = params.get("latencyMax");
  if (latencyMin && latencyMax) {
    filters.latencyRange = [parseFloat(latencyMin), parseFloat(latencyMax)];
  }

  // Sort
  const sortBy = params.get("sortBy");
  const sortOrder = params.get("sortOrder") as SortOrder | null;
  if (sortBy) {
    filters.sortBy = sortBy;
  }
  if (sortOrder) {
    filters.sortOrder = sortOrder;
  }

  return filters;
}

// Convert filter state to URL query string
function filtersToUrl(state: FilterState): string {
  const params = new URLSearchParams();

  if (state.dateRange) {
    params.append("startDate", state.dateRange.startDate);
    params.append("endDate", state.dateRange.endDate);
  } else if (state.timePreset) {
    params.append("timePreset", state.timePreset);
  }

  if (state.users) {
    params.append("users", state.users.join(","));
  }

  if (state.tools) {
    params.append("tools", state.tools.join(","));
  }

  if (state.complexities) {
    params.append("complexities", state.complexities.join(","));
  }

  if (state.successStatus !== "all") {
    params.append("successStatus", state.successStatus);
  }

  if (state.costRange) {
    params.append("costMin", state.costRange[0].toString());
    params.append("costMax", state.costRange[1].toString());
  }

  if (state.latencyRange) {
    params.append("latencyMin", state.latencyRange[0].toString());
    params.append("latencyMax", state.latencyRange[1].toString());
  }

  if (state.sortBy !== "cost") {
    params.append("sortBy", state.sortBy);
  }

  if (state.sortOrder !== "desc") {
    params.append("sortOrder", state.sortOrder);
  }

  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

interface FilterProviderProps {
  children: React.ReactNode;
}

export const FilterProvider: React.FC<FilterProviderProps> = ({ children }) => {
  // Initialize from URL on mount
  const [state, dispatch] = useReducer(filterReducer, defaultFilterState, (initial) => {
    const urlFilters = parseUrlToFilters(window.location.search);
    return { ...initial, ...urlFilters };
  });

  // Sync URL when state changes
  useEffect(() => {
    const url = filtersToUrl(state);
    window.history.replaceState(null, "", url || "/");
  }, [state]);

  // Convenience methods
  const setDateRange = useCallback((start: string, end: string) => {
    dispatch({
      type: "SET_DATE_RANGE",
      payload: { startDate: start, endDate: end },
    });
  }, []);

  const setTimePreset = useCallback((preset: TimePreset) => {
    dispatch({ type: "SET_TIME_PRESET", payload: preset });
  }, []);

  const setUsers = useCallback((users: string[] | null) => {
    dispatch({ type: "SET_USERS", payload: users });
  }, []);

  const setTools = useCallback((tools: string[] | null) => {
    dispatch({ type: "SET_TOOLS", payload: tools });
  }, []);

  const setComplexities = useCallback((complexities: ComplexityLevel[] | null) => {
    dispatch({ type: "SET_COMPLEXITIES", payload: complexities });
  }, []);

  const setSuccessStatus = useCallback((status: SuccessStatus) => {
    dispatch({ type: "SET_SUCCESS_STATUS", payload: status });
  }, []);

  const setCostRange = useCallback((min: number, max: number) => {
    dispatch({
      type: "SET_COST_RANGE",
      payload: [min, max],
    });
  }, []);

  const setLatencyRange = useCallback((min: number, max: number) => {
    dispatch({
      type: "SET_LATENCY_RANGE",
      payload: [min, max],
    });
  }, []);

  const setSort = useCallback((field: string, order: SortOrder) => {
    dispatch({
      type: "SET_SORT",
      payload: { field, order },
    });
  }, []);

  const resetAll = useCallback(() => {
    dispatch({ type: "RESET_ALL" });
  }, []);

  const getEffectiveDateRange = useCallback((): DateRange => {
    if (state.dateRange) {
      return state.dateRange;
    }
    return getDateRangeFromPreset(state.timePreset);
  }, [state.dateRange, state.timePreset]);

  const isFilterActive = useCallback((): boolean => {
    return (
      state.users !== null ||
      state.tools !== null ||
      state.complexities !== null ||
      state.successStatus !== "all" ||
      state.costRange !== null ||
      state.latencyRange !== null ||
      state.dateRange !== null ||
      state.timePreset !== "24h"
    );
  }, [state]);

  const value = useMemo<FilterContextType>(
    () => ({
      state,
      dispatch,
      setDateRange,
      setTimePreset,
      setUsers,
      setTools,
      setComplexities,
      setSuccessStatus,
      setCostRange,
      setLatencyRange,
      setSort,
      resetAll,
      getEffectiveDateRange,
      isFilterActive,
    }),
    [
      state,
      setDateRange,
      setTimePreset,
      setUsers,
      setTools,
      setComplexities,
      setSuccessStatus,
      setCostRange,
      setLatencyRange,
      setSort,
      resetAll,
      getEffectiveDateRange,
      isFilterActive,
    ]
  );

  return (
    <FilterContext.Provider value={value}>
      {children}
    </FilterContext.Provider>
  );
};

export const useFilterContext = (): FilterContextType => {
  const context = React.useContext(FilterContext);
  if (!context) {
    throw new Error("useFilterContext must be used within FilterProvider");
  }
  return context;
};
