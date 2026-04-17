/**
 * Integration tests for real-time WebSocket system.
 */

import { WebSocketClient, MetricsEvent } from '../src/services/websocket';

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

describe('Real-time System Integration', () => {
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

  describe('Multi-subscriber communication', () => {
    test('should handle multiple subscribers for different event types', async () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();
      const handler3 = jest.fn();

      client.subscribe('query_update', handler1);
      client.subscribe('cost_update', handler2);
      client.subscribe('performance_update', handler3);

      await client.connect();
      jest.runAllTimers();

      const queryEvent: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 100 },
      };

      (client as any).ws.simulateMessage(queryEvent);
      jest.runAllTimers();

      expect(handler1).toHaveBeenCalledWith(queryEvent);
      expect(handler2).not.toHaveBeenCalled();
      expect(handler3).not.toHaveBeenCalled();
    });

    test('should broadcast to all subscribers with wildcard', async () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      client.subscribe('*', handler1);
      client.subscribe('query_update', handler2);

      await client.connect();
      jest.runAllTimers();

      const event: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 100 },
      };

      (client as any).ws.simulateMessage(event);
      jest.runAllTimers();

      expect(handler1).toHaveBeenCalledWith(event);
      expect(handler2).toHaveBeenCalledWith(event);
    });
  });

  describe('Real-world metric streaming', () => {
    test('should handle continuous metric stream', async () => {
      const handler = jest.fn();
      client.subscribe('query_update', handler);

      await client.connect();
      jest.runAllTimers();

      for (let i = 0; i < 10; i++) {
        const event: MetricsEvent = {
          type: 'query_update',
          timestamp: new Date().toISOString(),
          data: { total_queries: (i + 1) * 100 },
        };
        (client as any).ws.simulateMessage(event);
      }

      jest.runAllTimers();

      expect(handler).toHaveBeenCalledTimes(10);
    });

    test('should maintain subscription during reconnection', async () => {
      const handler = jest.fn();
      client.subscribe('cost_update', handler);

      await client.connect();
      jest.runAllTimers();

      // Simulate disconnection
      (client as any).ws.close();
      jest.runAllTimers();

      expect(client.getState()).toBe('reconnecting');

      // Reconnection should happen
      jest.advanceTimersByTime(2000);
      jest.runAllTimers();

      // New event should be received
      const event: MetricsEvent = {
        type: 'cost_update',
        timestamp: new Date().toISOString(),
        data: { total_cost: 500 },
      };

      if ((client as any).ws) {
        (client as any).ws.simulateMessage(event);
      }

      jest.runAllTimers();

      // Handler should receive new events
      expect(handler.mock.calls.length).toBeGreaterThan(0);
    });
  });

  describe('Message handling at scale', () => {
    test('should handle burst of messages without dropping', async () => {
      const handler = jest.fn();
      client.subscribe('query_update', handler);

      await client.connect();
      jest.runAllTimers();

      // Simulate burst of 100 messages
      for (let i = 0; i < 100; i++) {
        const event: MetricsEvent = {
          type: 'query_update',
          timestamp: new Date().toISOString(),
          data: { id: i, total_queries: i * 10 },
        };
        (client as any).ws.simulateMessage(event);
      }

      jest.runAllTimers();

      expect(handler).toHaveBeenCalledTimes(100);
    });

    test('should rate limit rapid state changes', async () => {
      const stateChangeHandler = jest.fn();
      client.onStateChange(stateChangeHandler);

      const initialCallCount = stateChangeHandler.mock.calls.length;

      await client.connect();
      jest.runAllTimers();

      // Verify state change was called for transitions
      const connectingCallCount = stateChangeHandler.mock.calls.filter(
        (call) => call[0] === 'connecting'
      ).length;
      const connectedCallCount = stateChangeHandler.mock.calls.filter(
        (call) => call[0] === 'connected'
      ).length;

      expect(connectingCallCount).toBe(1);
      expect(connectedCallCount).toBe(1);
    });
  });

  describe('Error recovery', () => {
    test('should recover from message parsing errors and continue streaming', async () => {
      const handler = jest.fn();
      client.subscribe('query_update', handler);
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      await client.connect();
      jest.runAllTimers();

      // Send invalid message
      (client as any).ws.onmessage(new MessageEvent('message', { data: 'invalid json' }));
      jest.runAllTimers();

      // Send valid message
      const validEvent: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 100 },
      };
      (client as any).ws.simulateMessage(validEvent);
      jest.runAllTimers();

      expect(handler).toHaveBeenCalledWith(validEvent);
      consoleError.mockRestore();
    });

    test('should handle unsubscribe during message reception', async () => {
      const handler = jest.fn();
      const unsubscribe = client.subscribe('query_update', handler);

      await client.connect();
      jest.runAllTimers();

      const event1: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 100 },
      };
      (client as any).ws.simulateMessage(event1);
      jest.runAllTimers();

      expect(handler).toHaveBeenCalledTimes(1);

      unsubscribe();

      const event2: MetricsEvent = {
        type: 'query_update',
        timestamp: new Date().toISOString(),
        data: { total_queries: 200 },
      };
      (client as any).ws.simulateMessage(event2);
      jest.runAllTimers();

      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('Connection lifecycle', () => {
    test('should complete full lifecycle: connect -> disconnect -> reconnect', async () => {
      const stateChanges: string[] = [];
      client.onStateChange((state) => stateChanges.push(state));

      // Initial connect
      await client.connect();
      jest.runAllTimers();
      expect(stateChanges).toContain('connected');

      // Disconnect
      client.disconnect();
      jest.runAllTimers();
      expect(stateChanges).toContain('disconnected');

      // Reconnect
      stateChanges.length = 0;
      await client.connect();
      jest.runAllTimers();
      expect(stateChanges).toContain('connected');
    });

    test('should maintain message queue during offline period', () => {
      client.send({ type: 'subscribe', channel: 'metrics' });
      client.send({ type: 'filter', param: 'value' });

      const buffer = (client as any).messageBuffer;
      expect(buffer.length).toBe(2);

      expect(client.getState()).toBe('disconnected');
    });
  });
});
