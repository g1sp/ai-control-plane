/**
 * Filter state types for advanced analytics filtering
 */

export type ComplexityLevel = "SIMPLE" | "MODERATE" | "COMPLEX" | "VERY_COMPLEX";
export type TimePreset = "1h" | "24h" | "7d" | "30d";
export type SuccessStatus = "all" | "success" | "failed";
export type SortOrder = "asc" | "desc";

export interface DateRange {
  startDate: string;  // YYYY-MM-DD
  endDate: string;    // YYYY-MM-DD
}

export interface FilterState {
  // Date/Time filtering
  dateRange: DateRange | null;        // null = use timePreset
  timePreset: TimePreset | null;      // null = use dateRange

  // Dimension filtering
  users: string[] | null;             // null = all users
  tools: string[] | null;             // null = all tools
  complexities: ComplexityLevel[] | null;  // null = all complexities

  // Status filtering
  successStatus: SuccessStatus;

  // Range filtering
  costRange: [number, number] | null;       // [min, max] or null
  latencyRange: [number, number] | null;    // [min, max] in ms or null

  // Sorting
  sortBy: string;           // field name (e.g., "cost", "latency", "count")
  sortOrder: SortOrder;
}

export interface FilterAction {
  type: "SET_DATE_RANGE" | "SET_TIME_PRESET" | "SET_USERS" | "SET_TOOLS" |
         "SET_COMPLEXITIES" | "SET_SUCCESS_STATUS" | "SET_COST_RANGE" |
         "SET_LATENCY_RANGE" | "SET_SORT" | "RESET_ALL" | "LOAD_FROM_URL";
  payload?: any;
}

export interface FilterContextType {
  state: FilterState;
  dispatch: (action: FilterAction) => void;
  // Convenience methods
  setDateRange: (start: string, end: string) => void;
  setTimePreset: (preset: TimePreset) => void;
  setUsers: (users: string[] | null) => void;
  setTools: (tools: string[] | null) => void;
  setComplexities: (complexities: ComplexityLevel[] | null) => void;
  setSuccessStatus: (status: SuccessStatus) => void;
  setCostRange: (min: number, max: number) => void;
  setLatencyRange: (min: number, max: number) => void;
  setSort: (field: string, order: SortOrder) => void;
  resetAll: () => void;
  // Get current effective values
  getEffectiveDateRange: () => DateRange;
  isFilterActive: () => boolean;
}

export const defaultFilterState: FilterState = {
  dateRange: null,
  timePreset: "24h",
  users: null,
  tools: null,
  complexities: null,
  successStatus: "all",
  costRange: null,
  latencyRange: null,
  sortBy: "cost",
  sortOrder: "desc",
};
