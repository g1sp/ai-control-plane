/**
 * Tests for useRealtimeSubscription hook.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useRealtimeSubscription } from '../src/hooks/useRealtimeSubscription';
import { MetricsEvent } from '../src/services/websocket';

// Mock useRealtimeMetrics
jest.mock('../src/hooks/useRealtimeMetrics', () => ({
  useRealtimeMetrics: jest.fn().mockReturnValue({
    connectionState: 'connected',
    isConnected: true,
    isReconnecting: false,
    error: null,
    subscribe: jest.fn((eventType, handler) => {
      // Simulate receiving an event after a short delay
      setTimeout(() => {
        handler({
          type: eventType,
          timestamp: new Date().toISOString(),
          data: { test: 'value' },
        });
      }, 10);
      return jest.fn();
    }),
    onStateChange: jest.fn(() => jest.fn()),
  }),
}));

describe('useRealtimeSubscription', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('should initialize with null data and loading state', () => {
    const { result } = renderHook(() => useRealtimeSubscription('query_update', 'user1'));

    expect(result.current.data).toBe(null);
    expect(result.current.isLoading).toBe(true);
    expect(result.current.lastUpdate).toBe(null);
    expect(result.current.error).toBe(null);
  });

  test('should not load when disconnected', () => {
    const useRealtimeMetricsMock = require('../src/hooks/useRealtimeMetrics').useRealtimeMetrics;
    useRealtimeMetricsMock.mockReturnValueOnce({
      connectionState: 'disconnected',
      isConnected: false,
      isReconnecting: false,
      error: null,
      subscribe: jest.fn(),
      onStateChange: jest.fn(),
    });

    const { result } = renderHook(() => useRealtimeSubscription('query_update', 'user1'));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBe(null);
  });

  test('should receive and store subscription data', async () => {
    const { result } = renderHook(() => useRealtimeSubscription('query_update', 'user1'));

    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.data).not.toBe(null);
    });

    expect(result.current.data).toEqual({ test: 'value' });
    expect(result.current.isLoading).toBe(false);
  });

  test('should transform event data using provided transform function', async () => {
    const transform = jest.fn((event: MetricsEvent) => ({
      transformed: true,
      original: event.data,
    }));

    const { result } = renderHook(() => useRealtimeSubscription('cost_update', 'user1', transform));

    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.data).not.toBe(null);
    });

    expect(transform).toHaveBeenCalled();
    expect(result.current.data).toEqual({
      transformed: true,
      original: { test: 'value' },
    });
  });

  test('should update lastUpdate timestamp when data changes', async () => {
    const { result } = renderHook(() => useRealtimeSubscription('query_update', 'user1'));

    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.lastUpdate).not.toBe(null);
    });

    const firstUpdate = result.current.lastUpdate;
    expect(firstUpdate).toBeInstanceOf(Date);
  });

  test('should handle transform errors gracefully', async () => {
    const transform = jest.fn(() => {
      throw new Error('Transform failed');
    });

    const { result } = renderHook(() => useRealtimeSubscription('query_update', 'user1', transform));

    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.error).not.toBe(null);
    });

    expect(result.current.error?.message).toBe('Transform failed');
    expect(result.current.isLoading).toBe(false);
  });

  test('should clear error when successful update received after error', async () => {
    const useRealtimeMetricsMock = require('../src/hooks/useRealtimeMetrics').useRealtimeMetrics;
    let currentHandler: ((event: MetricsEvent) => void) | null = null;

    useRealtimeMetricsMock.mockReturnValueOnce({
      connectionState: 'connected',
      isConnected: true,
      isReconnecting: false,
      error: null,
      subscribe: jest.fn((eventType, handler) => {
        currentHandler = handler;
        return jest.fn();
      }),
      onStateChange: jest.fn(),
    });

    const { result, rerender } = renderHook(() => useRealtimeSubscription('query_update', 'user1'));

    // Simulate error
    if (currentHandler) {
      currentHandler({
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { invalid: Symbol() }, // This would cause JSON serialization error
      } as any);
    }

    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.error).not.toBe(null);
    });

    // Reset handler for successful message
    useRealtimeMetricsMock.mockReturnValueOnce({
      connectionState: 'connected',
      isConnected: true,
      isReconnecting: false,
      error: null,
      subscribe: jest.fn((eventType, handler) => {
        handler({
          type: eventType,
          timestamp: new Date().toISOString(),
          data: { valid: 'data' },
        });
        return jest.fn();
      }),
      onStateChange: jest.fn(),
    });

    rerender();
    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.error).toBe(null);
      expect(result.current.data).toEqual({ valid: 'data' });
    });
  });

  test('should handle multiple event types', async () => {
    const { result: result1 } = renderHook(() => useRealtimeSubscription('query_update', 'user1'));
    const { result: result2 } = renderHook(() => useRealtimeSubscription('cost_update', 'user1'));

    jest.runAllTimers();

    await waitFor(() => {
      expect(result1.current.data).not.toBe(null);
      expect(result2.current.data).not.toBe(null);
    });

    expect(result1.current.data).toBeDefined();
    expect(result2.current.data).toBeDefined();
  });

  test('should resubscribe when user ID changes', () => {
    const useRealtimeMetricsMock = require('../src/hooks/useRealtimeMetrics').useRealtimeMetrics;
    const mockSubscribe = jest.fn(() => jest.fn());

    useRealtimeMetricsMock.mockReturnValue({
      connectionState: 'connected',
      isConnected: true,
      isReconnecting: false,
      error: null,
      subscribe: mockSubscribe,
      onStateChange: jest.fn(),
    });

    const { rerender } = renderHook(
      ({ userId }) => useRealtimeSubscription('query_update', userId),
      { initialProps: { userId: 'user1' } }
    );

    const firstCallCount = mockSubscribe.mock.calls.length;

    rerender({ userId: 'user2' });

    expect(mockSubscribe.mock.calls.length).toBeGreaterThan(firstCallCount);
  });

  test('should use generic type parameter', async () => {
    interface QueryMetrics {
      total_queries: number;
      success_rate: number;
    }

    const transform = (event: MetricsEvent) => ({
      total_queries: 100,
      success_rate: 0.95,
    } as QueryMetrics);

    const { result } = renderHook(() =>
      useRealtimeSubscription<QueryMetrics>('query_update', 'user1', transform)
    );

    jest.runAllTimers();

    await waitFor(() => {
      expect(result.current.data).not.toBe(null);
    });

    const data = result.current.data as QueryMetrics;
    expect(data.total_queries).toBe(100);
    expect(data.success_rate).toBe(0.95);
  });
});
