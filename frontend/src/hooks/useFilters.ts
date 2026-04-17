/**
 * Custom hook for accessing filter context
 */

import { useFilterContext } from "../context/FilterContext";

export const useFilters = () => {
  return useFilterContext();
};
