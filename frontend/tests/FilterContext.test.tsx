/**
 * Tests for FilterContext and filter state management
 */

import { renderHook, act } from "@testing-library/react";
import { FilterProvider } from "../src/context/FilterContext";
import { useFilters } from "../src/hooks/useFilters";

describe("FilterContext", () => {
  const wrapper = ({ children }: any) => <FilterProvider>{children}</FilterProvider>;

  describe("Time Range Management", () => {
    test("should initialize with default time preset (24h)", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.state.timePreset).toBe("24h");
      expect(result.current.state.dateRange).toBeNull();
    });

    test("should change time preset", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setTimePreset("7d");
      });

      expect(result.current.state.timePreset).toBe("7d");
    });

    test("should set custom date range and clear time preset", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setDateRange("2026-04-01", "2026-04-15");
      });

      expect(result.current.state.dateRange).toEqual({
        startDate: "2026-04-01",
        endDate: "2026-04-15",
      });
      expect(result.current.state.timePreset).toBeNull();
    });

    test("should get effective date range", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      // With default preset (24h), effective range should be recent
      const range1 = result.current.getEffectiveDateRange();
      expect(range1.startDate).toBeLessThan(range1.endDate);

      // With custom range
      act(() => {
        result.current.setDateRange("2026-04-01", "2026-04-15");
      });

      const range2 = result.current.getEffectiveDateRange();
      expect(range2.startDate).toBe("2026-04-01");
      expect(range2.endDate).toBe("2026-04-15");
    });
  });

  describe("Dimension Filtering", () => {
    test("should set and clear users filter", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setUsers(["user1", "user2"]);
      });

      expect(result.current.state.users).toEqual(["user1", "user2"]);

      act(() => {
        result.current.setUsers(null);
      });

      expect(result.current.state.users).toBeNull();
    });

    test("should set and clear tools filter", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setTools(["tool1", "tool2"]);
      });

      expect(result.current.state.tools).toEqual(["tool1", "tool2"]);

      act(() => {
        result.current.setTools(null);
      });

      expect(result.current.state.tools).toBeNull();
    });

    test("should set and clear complexities filter", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setComplexities(["SIMPLE", "MODERATE"]);
      });

      expect(result.current.state.complexities).toEqual(["SIMPLE", "MODERATE"]);

      act(() => {
        result.current.setComplexities(null);
      });

      expect(result.current.state.complexities).toBeNull();
    });
  });

  describe("Status Filtering", () => {
    test("should set success status", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.state.successStatus).toBe("all");

      act(() => {
        result.current.setSuccessStatus("success");
      });

      expect(result.current.state.successStatus).toBe("success");

      act(() => {
        result.current.setSuccessStatus("failed");
      });

      expect(result.current.state.successStatus).toBe("failed");
    });
  });

  describe("Range Filtering", () => {
    test("should set and clear cost range", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setCostRange(10, 100);
      });

      expect(result.current.state.costRange).toEqual([10, 100]);

      act(() => {
        result.current.setCostRange(0, 1000);
      });

      expect(result.current.state.costRange).toBeNull();
    });

    test("should set and clear latency range", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setLatencyRange(100, 500);
      });

      expect(result.current.state.latencyRange).toEqual([100, 500]);

      act(() => {
        result.current.setLatencyRange(0, 5000);
      });

      expect(result.current.state.latencyRange).toBeNull();
    });
  });

  describe("Sorting", () => {
    test("should set sort field and order", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setSort("latency", "asc");
      });

      expect(result.current.state.sortBy).toBe("latency");
      expect(result.current.state.sortOrder).toBe("asc");
    });

    test("should have default sort (cost, desc)", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.state.sortBy).toBe("cost");
      expect(result.current.state.sortOrder).toBe("desc");
    });
  });

  describe("Filter Status", () => {
    test("should detect active filters", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      expect(result.current.isFilterActive()).toBe(false);

      act(() => {
        result.current.setUsers(["user1"]);
      });

      expect(result.current.isFilterActive()).toBe(true);
    });

    test("should return false for default state only", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      // Default: 24h preset, all status
      expect(result.current.isFilterActive()).toBe(false);

      // Change to 7d
      act(() => {
        result.current.setTimePreset("7d");
      });

      expect(result.current.isFilterActive()).toBe(true);
    });
  });

  describe("Reset All", () => {
    test("should reset all filters to default", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setUsers(["user1"]);
        result.current.setTools(["tool1"]);
        result.current.setComplexities(["SIMPLE"]);
        result.current.setSuccessStatus("failed");
        result.current.setCostRange(50, 500);
        result.current.setLatencyRange(200, 1000);
      });

      expect(result.current.isFilterActive()).toBe(true);

      act(() => {
        result.current.resetAll();
      });

      expect(result.current.state.users).toBeNull();
      expect(result.current.state.tools).toBeNull();
      expect(result.current.state.complexities).toBeNull();
      expect(result.current.state.successStatus).toBe("all");
      expect(result.current.state.costRange).toBeNull();
      expect(result.current.state.latencyRange).toBeNull();
      expect(result.current.state.timePreset).toBe("24h");
      expect(result.current.isFilterActive()).toBe(false);
    });
  });

  describe("URL Synchronization", () => {
    test("should serialize filters to URL query string", () => {
      const { result } = renderHook(() => useFilters(), { wrapper });

      act(() => {
        result.current.setUsers(["user1", "user2"]);
        result.current.setTimePreset("7d");
        result.current.setSuccessStatus("success");
      });

      const url = window.location.href;
      expect(url).toContain("users=user1");
      expect(url).toContain("timePreset=7d");
      expect(url).toContain("successStatus=success");
    });
  });
});
