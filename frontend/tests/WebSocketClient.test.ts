/**
 * Tests for WebSocketClient real-time connection management.
 */

import { WebSocketClient, MetricsEvent } from '../src/services/websocket';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  sent: string[] = [];

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.();
    }, 10);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    setTimeout(() => {
      this.onclose?.();
    }, 10);
  }

  simulateMessage(data: any) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }

  simulateError() {
    this.onerror?.(new Event('error'));
    this.close();
  }
}

global.WebSocket = MockWebSocket as any;

describe('WebSocketClient', () => {
  let client: WebSocketClient;

  beforeEach(() => {
    jest.clearAllTimers();
    jest.useFakeTimers();
    client = new WebSocketClient('ws://localhost:8000/api/v1/analytics/stream/user1');
  });

  afterEach(() => {
    client.disconnect();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Connection Lifecycle', () => {
    test('should connect and reach connected state', async () => {
      const stateChanges: string[] = [];
      client.onStateChange((state) => stateChanges.push(state));

      await client.connect();
      jest.runAllTimers();

      expect(stateChanges).toContain('connecting');
      expect(stateChanges).toContain('connected');
      expect(client.isConnected()).toBe(true);
    });

    test('should handle disconnect', async () => {
      await client.connect();
      jest.runAllTimers();

      const stateChanges: string[] = [];
      client.onStateChange((state) => stateChanges.push(state));

      client.disconnect();
      jest.runAllTimers();

      expect(client.getState()).toBe('disconnected');
      expect(stateChanges).toContain('disconnected');
    });

    test('should not reconnect if multiple connect calls', async () => {
      await client.connect();
      jest.runAllTimers();

      const connectPromise1 = client.connect();
      const connectPromise2 = client.connect();
      jest.runAllTimers();

      await connectPromise1;
      await connectPromise2;

      expect(client.isConnected()).toBe(true);
    });
  });

  describe('Message Handling', () => {
    test('should parse and emit messages', async () => {
      const handler = jest.fn();
      client.subscribe('query_update', handler);

      await client.connect();
      jest.runAllTimers();

      const testEvent: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 100 },
      };

      (client as any).ws.simulateMessage(testEvent);
      jest.runAllTimers();

      expect(handler).toHaveBeenCalledWith(testEvent);
    });

    test('should emit to wildcard subscribers', async () => {
      const handler = jest.fn();
      client.subscribe('*', handler);

      await client.connect();
      jest.runAllTimers();

      const testEvent: MetricsEvent = {
        type: 'cost_update',
        timestamp: new Date().toISOString(),
        data: { total_cost: 150.0 },
      };

      (client as any).ws.simulateMessage(testEvent);
      jest.runAllTimers();

      expect(handler).toHaveBeenCalledWith(testEvent);
    });

    test('should handle multiple subscribers for same event', async () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();
      client.subscribe('performance_update', handler1);
      client.subscribe('performance_update', handler2);

      await client.connect();
      jest.runAllTimers();

      const testEvent: MetricsEvent = {
        type: 'performance_update',
        timestamp: new Date().toISOString(),
        data: { avg_latency: 150 },
      };

      (client as any).ws.simulateMessage(testEvent);
      jest.runAllTimers();

      expect(handler1).toHaveBeenCalledWith(testEvent);
      expect(handler2).toHaveBeenCalledWith(testEvent);
    });

    test('should unsubscribe and stop receiving messages', async () => {
      const handler = jest.fn();
      const unsubscribe = client.subscribe('query_update', handler);

      await client.connect();
      jest.runAllTimers();

      unsubscribe();

      const testEvent: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 100 },
      };

      (client as any).ws.simulateMessage(testEvent);
      jest.runAllTimers();

      expect(handler).not.toHaveBeenCalled();
    });

    test('should handle invalid JSON messages gracefully', async () => {
      const handler = jest.fn();
      client.subscribe('*', handler);
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      await client.connect();
      jest.runAllTimers();

      (client as any).ws.onmessage(new MessageEvent('message', { data: 'invalid json' }));
      jest.runAllTimers();

      expect(consoleError).toHaveBeenCalled();
      expect(handler).not.toHaveBeenCalled();

      consoleError.mockRestore();
    });
  });

  describe('Reconnection Strategy', () => {
    test('should reconnect with exponential backoff', async () => {
      const stateChanges: string[] = [];
      client.onStateChange((state) => stateChanges.push(state));

      await client.connect();
      jest.runAllTimers();

      // Simulate connection close
      (client as any).ws.close();
      jest.runAllTimers();

      expect(stateChanges).toContain('reconnecting');
    });

    test('should respect max reconnection attempts', async () => {
      await client.connect();
      jest.runAllTimers();

      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      for (let i = 0; i < 6; i++) {
        (client as any).ws.close();
        jest.advanceTimersByTime(1000);
      }

      expect(client.getState()).toBe('error');
      consoleError.mockRestore();
    });

    test('should reset reconnect attempts on successful connection', async () => {
      await client.connect();
      jest.runAllTimers();

      (client as any).reconnectAttempts = 2;

      // Simulate close and reconnect
      (client as any).ws.close();
      jest.advanceTimersByTime(1000);

      expect((client as any).reconnectAttempts).toBe(2);

      // Wait for reconnection
      jest.runAllTimers();

      // Should reset after successful connection
      expect((client as any).reconnectAttempts).toBe(0);
    });
  });

  describe('Heartbeat Mechanism', () => {
    test('should send heartbeat ping periodically', async () => {
      await client.connect();
      jest.runAllTimers();

      const ws = (client as any).ws;
      ws.sent = [];

      jest.advanceTimersByTime(30000);

      expect(ws.sent.length).toBeGreaterThan(0);
      expect(ws.sent.some((msg: string) => msg.includes('ping'))).toBe(true);
    });

    test('should disconnect on heartbeat timeout', async () => {
      await client.connect();
      jest.runAllTimers();

      // Advance past heartbeat interval
      jest.advanceTimersByTime(60000);

      expect(client.getState()).not.toBe('connected');
    });

    test('should reset heartbeat timeout on message received', async () => {
      await client.connect();
      jest.runAllTimers();

      jest.advanceTimersByTime(55000);
      (client as any).ws.simulateMessage({ type: 'ping' });

      // Should not disconnect for another 60 seconds
      jest.advanceTimersByTime(5000);
      expect(client.isConnected()).toBe(true);
    });
  });

  describe('Message Sending', () => {
    test('should send messages when connected', async () => {
      await client.connect();
      jest.runAllTimers();

      client.send({ type: 'subscribe', channel: 'metrics' });
      jest.runAllTimers();

      const ws = (client as any).ws;
      expect(ws.sent.length).toBeGreaterThan(0);
    });

    test('should buffer messages when disconnected', () => {
      client.send({ type: 'subscribe', channel: 'metrics' });
      jest.runAllTimers();

      const buffer = (client as any).messageBuffer;
      expect(buffer.length).toBe(1);
    });

    test('should flush buffered messages on connection', async () => {
      client.send({ type: 'subscribe', channel: 'metrics' });
      jest.runAllTimers();

      await client.connect();
      jest.runAllTimers();

      const ws = (client as any).ws;
      expect(ws.sent.length).toBeGreaterThan(0);
    });

    test('should respect buffer size limit', () => {
      for (let i = 0; i < 150; i++) {
        client.send({ type: 'msg', id: i });
      }
      jest.runAllTimers();

      const buffer = (client as any).messageBuffer;
      expect(buffer.length).toBeLessThanOrEqual(100);
    });
  });

  describe('State Management', () => {
    test('should notify state change handlers', async () => {
      const handler = jest.fn();
      client.onStateChange(handler);

      await client.connect();
      jest.runAllTimers();

      expect(handler).toHaveBeenCalledWith('connecting');
      expect(handler).toHaveBeenCalledWith('connected');
    });

    test('should not duplicate state changes', async () => {
      const handler = jest.fn();
      client.onStateChange(handler);

      await client.connect();
      jest.runAllTimers();

      const callCount = handler.mock.calls.length;
      jest.advanceTimersByTime(1000);

      // Should not call handler again for same state
      expect(handler.mock.calls.length).toBe(callCount);
    });

    test('should return correct connection state', async () => {
      expect(client.getState()).toBe('disconnected');
      expect(client.isConnected()).toBe(false);

      await client.connect();
      jest.runAllTimers();

      expect(client.getState()).toBe('connected');
      expect(client.isConnected()).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test('should handle WebSocket errors', async () => {
      const stateChanges: string[] = [];
      client.onStateChange((state) => stateChanges.push(state));

      const connectPromise = client.connect();
      jest.advanceTimersByTime(100);

      (client as any).ws.simulateError();
      jest.runAllTimers();

      await expect(connectPromise).rejects.toThrow();
      expect(stateChanges).toContain('error');
    });

    test('should set error state on connection failure', async () => {
      const connectPromise = client.connect();
      jest.advanceTimersByTime(100);

      (client as any).ws.simulateError();
      jest.runAllTimers();

      await expect(connectPromise).rejects.toThrow();
      expect(client.getState()).toBe('error');
    });
  });
});
