/**
 * React hooks for analytics data fetching
 */

import { useState, useEffect } from "react";
import analyticsAPI from "../services/analyticsAPI";

export const useQueryAnalytics = (hours: number = 24) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getQueryAnalytics(hours)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [hours]);

  return { data, loading, error };
};

export const useAllUsersMetrics = (hours: number = 24) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getAllUsersMetrics(hours)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [hours]);

  return { data, loading, error };
};

export const useUserMetrics = (userId: string, hours: number = 24) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    analyticsAPI
      .getUserMetrics(userId, hours)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId, hours]);

  return { data, loading, error };
};

export const useAllToolsAnalytics = (hours: number = 24) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getAllToolsAnalytics(hours)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [hours]);

  return { data, loading, error };
};

export const useDailyCosts = (days: number = 30) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getDailyCosts(days)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [days]);

  return { data, loading, error };
};

export const useCostForecast = (daysAhead: number = 7, lookbackDays: number = 30) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getForecastedCost(daysAhead, lookbackDays)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [daysAhead, lookbackDays]);

  return { data, loading, error };
};

export const useLatencyMetrics = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getLatencyMetrics()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
};

export const useStreamingSessionsAnalytics = (hours: number = 24) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    analyticsAPI
      .getStreamingSessionsAnalytics(hours)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [hours]);

  return { data, loading, error };
};
