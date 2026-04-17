/**
 * Custom hooks for filtered analytics data
 */

import { useEffect, useState } from "react";
import { useFilters } from "./useFilters";
import { AnalyticsAPIClient, FilteredQueryResponse, FilteredUserCostsResponse } from "../services/analyticsAPI";

const client = new AnalyticsAPIClient();

interface FilteredQueryState {
  data: FilteredQueryResponse | null;
  loading: boolean;
  error: string | null;
}

interface FilteredCostState {
  data: FilteredUserCostsResponse | null;
  loading: boolean;
  error: string | null;
}

export const useFilteredQueries = (pageSize: number = 50) => {
  const filters = useFilters();
  const [state, setState] = useState<FilteredQueryState>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const fetchFilteredQueries = async () => {
      setState({ data: null, loading: true, error: null });

      try {
        const effectiveDateRange = filters.getEffectiveDateRange();

        // Convert date range to hours for simplicity
        // (in production, would pass actual dates to backend)
        const preset = filters.state.timePreset || "24h";
        const hours = preset === "1h" ? 1 : preset === "24h" ? 24 : preset === "7d" ? 168 : 720;

        const response = await client.getFilteredQueries(
          hours,
          filters.state.complexities || undefined,
          filters.state.successStatus,
          filters.state.costRange?.[0],
          filters.state.costRange?.[1],
          filters.state.latencyRange?.[0],
          filters.state.latencyRange?.[1],
          filters.state.sortBy,
          filters.state.sortOrder,
          pageSize,
          0
        );

        setState({ data: response, loading: false, error: null });
      } catch (err) {
        setState({
          data: null,
          loading: false,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    };

    fetchFilteredQueries();
  }, [filters.state, pageSize]);

  return state;
};

export const useFilteredUserCosts = (pageSize: number = 50) => {
  const filters = useFilters();
  const [state, setState] = useState<FilteredCostState>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const fetchFilteredCosts = async () => {
      setState({ data: null, loading: true, error: null });

      try {
        const response = await client.getFilteredUserCosts(
          30,
          filters.state.costRange?.[0],
          filters.state.costRange?.[1],
          filters.state.sortBy,
          filters.state.sortOrder,
          pageSize,
          0
        );

        setState({ data: response, loading: false, error: null });
      } catch (err) {
        setState({
          data: null,
          loading: false,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    };

    fetchFilteredCosts();
  }, [filters.state, pageSize]);

  return state;
};
