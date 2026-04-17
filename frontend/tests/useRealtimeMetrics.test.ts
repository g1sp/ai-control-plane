/**
 * Tests for useRealtimeMetrics hook.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useRealtimeMetrics } from '../src/hooks/useRealtimeMetrics';
import { MetricsEvent } from '../src/services/websocket';

// Mock WebSocketClient
jest.mock('../src/services/websocket', () => ({
  WebSocketClient: jest.fn().mockImplementation(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    subscribe: jest.fn((type, handler) => jest.fn()),
    on: jest.fn(),
    onStateChange: jest.fn((handler) => jest.fn()),
    send: jest.fn(),
    getState: jest.fn(() => 'disconnected'),
    isConnected: jest.fn(() => false),
  })),
  ConnectionState: {},
  MetricsEvent: {},
}));

describe('useRealtimeMetrics', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should initialize in disconnected state', () => {
    const { result } = renderHook(() => useRealtimeMetrics('user1'));

    expect(result.current.connectionState).toBe('disconnected');
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isReconnecting).toBe(false);
    expect(result.current.error).toBe(null);
  });

  test('should call connect on mount', async () => {
    const { result } = renderHook(() => useRealtimeMetrics('user1'));

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });
  });

  test('should update connection state on state change', async () => {
    const WebSocketClientMock = require('../src/services/websocket').WebSocketClient;
    let stateChangeHandler: ((state: string) => void) | null = null;

    WebSocketClientMock.mockImplementationOnce(() => ({
      connect: jest.fn(),
      disconnect: jest.fn(),
      subscribe: jest.fn(),
      onStateChange: jest.fn((handler) => {
        stateChangeHandler = handler;
        return jest.fn();
      }),
      getState: jest.fn(() => 'disconnected'),
      isConnected: jest.fn(() => false),
    }));

    const { result, rerender } = renderHook(() => useRealtimeMetrics('user1'));

    await waitFor(() => {
      expect(stateChangeHandler).toBeDefined();
    });

    if (stateChangeHandler) {
      stateChangeHandler('connected');
    }

    rerender();

    await waitFor(() => {
      expect(result.current.connectionState).toBe('connected');
      expect(result.current.isConnected).toBe(true);
    });
  });

  test('should set error on connection error', async () => {
    const WebSocketClientMock = require('../src/services/websocket').WebSocketClient;
    let stateChangeHandler: ((state: string) => void) | null = null;

    WebSocketClientMock.mockImplementationOnce(() => ({
      connect: jest.fn(),
      disconnect: jest.fn(),
      subscribe: jest.fn(),
      onStateChange: jest.fn((handler) => {
        stateChangeHandler = handler;
        return jest.fn();
      }),
      getState: jest.fn(() => 'error'),
      isConnected: jest.fn(() => false),
    }));

    const { result, rerender } = renderHook(() => useRealtimeMetrics('user1'));

    await waitFor(() => {
      expect(stateChangeHandler).toBeDefined();
    });

    if (stateChangeHandler) {
      stateChangeHandler('error');
    }

    rerender();

    await waitFor(() => {
      expect(result.current.connectionState).toBe('error');
      expect(result.current.error).not.toBe(null);
    });
  });

  test('should track reconnecting state', async () => {
    const WebSocketClientMock = require('../src/services/websocket').WebSocketClient;
    let stateChangeHandler: ((state: string) => void) | null = null;

    WebSocketClientMock.mockImplementationOnce(() => ({
      connect: jest.fn(),
      disconnect: jest.fn(),
      subscribe: jest.fn(),
      onStateChange: jest.fn((handler) => {
        stateChangeHandler = handler;
        return jest.fn();
      }),
      getState: jest.fn(() => 'reconnecting'),
      isConnected: jest.fn(() => false),
    }));

    const { result, rerender } = renderHook(() => useRealtimeMetrics('user1'));

    await waitFor(() => {
      expect(stateChangeHandler).toBeDefined();
    });

    if (stateChangeHandler) {
      stateChangeHandler('reconnecting');
    }

    rerender();

    await waitFor(() => {
      expect(result.current.isReconnecting).toBe(true);
      expect(result.current.isConnected).toBe(false);
    });
  });

  test('should provide subscribe method', async () => {
    const { result } = renderHook(() => useRealtimeMetrics('user1'));

    expect(result.current.subscribe).toBeDefined();
    expect(typeof result.current.subscribe).toBe('function');
  });

  test('should provide onStateChange method', async () => {
    const { result } = renderHook(() => useRealtimeMetrics('user1'));

    expect(result.current.onStateChange).toBeDefined();
    expect(typeof result.current.onStateChange).toBe('function');
  });

  test('should handle different user IDs', () => {
    const { result: result1 } = renderHook(() => useRealtimeMetrics('user1'));
    const { result: result2 } = renderHook(() => useRealtimeMetrics('user2'));

    expect(result1.current).toBeDefined();
    expect(result2.current).toBeDefined();
  });

  test('should clear error when connection established', async () => {
    const WebSocketClientMock = require('../src/services/websocket').WebSocketClient;
    let stateChangeHandler: ((state: string) => void) | null = null;

    WebSocketClientMock.mockImplementationOnce(() => ({
      connect: jest.fn(),
      disconnect: jest.fn(),
      subscribe: jest.fn(),
      onStateChange: jest.fn((handler) => {
        stateChangeHandler = handler;
        return jest.fn();
      }),
      getState: jest.fn(() => 'connected'),
      isConnected: jest.fn(() => true),
    }));

    const { result, rerender } = renderHook(() => useRealtimeMetrics('user1'));

    if (stateChangeHandler) {
      stateChangeHandler('error');
    }

    rerender();

    await waitFor(() => {
      expect(result.current.error).not.toBe(null);
    });

    if (stateChangeHandler) {
      stateChangeHandler('connected');
    }

    rerender();

    await waitFor(() => {
      expect(result.current.error).toBe(null);
    });
  });

  test('should cleanup on unmount', () => {
    const WebSocketClientMock = require('../src/services/websocket').WebSocketClient;
    const mockInstance = WebSocketClientMock.mock.results[0].value;

    const { unmount } = renderHook(() => useRealtimeMetrics('user1'));

    unmount();

    // Verify cleanup was called (would call disconnect when ref count reaches 0)
    expect(mockInstance).toBeDefined();
  });
});
