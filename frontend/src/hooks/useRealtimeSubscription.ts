/**
 * Hook for subscribing to specific metric event types with local state management.
 */

import { useEffect, useState, useCallback } from 'react';
import { MetricsEvent } from '../services/websocket';
import { useRealtimeMetrics } from './useRealtimeMetrics';

interface UseRealtimeSubscriptionReturn<T> {
  data: T | null;
  isLoading: boolean;
  lastUpdate: Date | null;
  error: Error | null;
}

export function useRealtimeSubscription<T = Record<string, any>>(
  eventType: string,
  userId: string,
  transform?: (event: MetricsEvent) => T
): UseRealtimeSubscriptionReturn<T> {
  const { subscribe, isConnected } = useRealtimeMetrics(userId);
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!isConnected) {
      setIsLoading(true);
      return;
    }

    const unsubscribe = subscribe(eventType, (event: MetricsEvent) => {
      try {
        const transformedData = transform ? transform(event) : (event.data as T);
        setData(transformedData);
        setLastUpdate(new Date());
        setError(null);
        setIsLoading(false);
      } catch (err) {
        setError(err as Error);
        setIsLoading(false);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [eventType, userId, isConnected, subscribe, transform]);

  return {
    data,
    isLoading,
    lastUpdate,
    error,
  };
}
