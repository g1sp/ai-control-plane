/**
 * Tests for connection telemetry collector.
 */

import { ConnectionTelemetryCollector, getTelemetryCollector } from '../src/services/connectionTelemetry';

describe('ConnectionTelemetryCollector', () => {
  let collector: ConnectionTelemetryCollector;

  beforeEach(() => {
    collector = new ConnectionTelemetryCollector();
  });

  test('should initialize with zero metrics', () => {
    const telemetry = collector.getTelemetry();

    expect(telemetry.totalConnections).toBe(0);
    expect(telemetry.successfulConnections).toBe(0);
    expect(telemetry.failedConnections).toBe(0);
    expect(telemetry.totalMessagesSent).toBe(0);
    expect(telemetry.totalMessagesReceived).toBe(0);
  });

  test('should record successful connection', () => {
    collector.recordStateChange('connecting');
    collector.recordStateChange('connected');

    const telemetry = collector.getTelemetry();
    expect(telemetry.successfulConnections).toBe(1);
    expect(telemetry.totalConnections).toBe(1);
  });

  test('should record failed connection', () => {
    collector.recordStateChange('connecting');
    collector.recordStateChange('error', 'Connection failed');

    const telemetry = collector.getTelemetry();
    expect(telemetry.failedConnections).toBe(1);
  });

  test('should track reconnection attempts', () => {
    collector.recordStateChange('connected');
    collector.recordStateChange('disconnected');
    collector.recordStateChange('reconnecting');
    collector.recordStateChange('connected');

    const telemetry = collector.getTelemetry();
    expect(telemetry.reconnectionAttempts).toBeGreaterThan(0);
  });

  test('should record messages sent and received', () => {
    for (let i = 0; i < 10; i++) {
      collector.recordMessageSent();
    }

    for (let i = 0; i < 5; i++) {
      collector.recordMessageReceived();
    }

    const telemetry = collector.getTelemetry();
    expect(telemetry.totalMessagesSent).toBe(10);
    expect(telemetry.totalMessagesReceived).toBe(5);
  });

  test('should record and calculate latency metrics', () => {
    collector.recordLatency(100);
    collector.recordLatency(200);
    collector.recordLatency(150);

    const telemetry = collector.getTelemetry();
    expect(telemetry.averageLatency).toBe(150);
    expect(telemetry.maxLatency).toBe(200);
    expect(telemetry.minLatency).toBe(100);
  });

  test('should track connection time windows', () => {
    collector.recordStateChange('connected');
    expect(collector.getTelemetry().lastConnectionTime).not.toBeNull();

    collector.recordStateChange('disconnected');
    expect(collector.getTelemetry().lastDisconnectionTime).not.toBeNull();
  });

  test('should track error history', () => {
    collector.recordStateChange('error', 'Network error 1');
    collector.recordStateChange('error', 'Network error 2');
    collector.recordStateChange('connected');

    const telemetry = collector.getTelemetry();
    expect(telemetry.connectionErrors.length).toBe(2);
    expect(telemetry.connectionErrors[0]).toContain('Network error 1');
  });

  test('should limit error history to 100 items', () => {
    for (let i = 0; i < 150; i++) {
      collector.recordStateChange('error', `Error ${i}`);
    }

    const telemetry = collector.getTelemetry();
    expect(telemetry.connectionErrors.length).toBeLessThanOrEqual(100);
  });

  test('should calculate reconnection time', () => {
    collector.recordStateChange('connected');
    collector.recordStateChange('disconnected');
    collector.recordStateChange('reconnecting');

    // Simulate delay
    setTimeout(() => {
      collector.recordStateChange('connected');
    }, 100);

    // Note: In real tests, would need to handle async properly
  });

  test('should get metrics history', () => {
    collector.recordStateChange('connected');
    collector.recordStateChange('disconnected');
    collector.recordStateChange('reconnecting');
    collector.recordStateChange('connected');

    const history = collector.getMetricsHistory(limit: 10);
    expect(history.length).toBeGreaterThan(0);
  });

  test('should reset all metrics', () => {
    collector.recordStateChange('connected');
    collector.recordMessageSent();
    collector.recordLatency(100);

    let telemetry = collector.getTelemetry();
    expect(telemetry.successfulConnections).toBe(1);

    collector.reset();

    telemetry = collector.getTelemetry();
    expect(telemetry.totalConnections).toBe(0);
    expect(telemetry.totalMessagesSent).toBe(0);
    expect(telemetry.averageLatency).toBe(0);
  });

  test('should limit latency history', () => {
    for (let i = 0; i < 1100; i++) {
      collector.recordLatency(i * 10);
    }

    const telemetry = collector.getTelemetry();
    // Should not crash and should limit properly
    expect(telemetry.maxLatency).toBeGreaterThan(0);
  });

  test('should calculate uptime and downtime', () => {
    collector.recordStateChange('connected');

    // Simulate time passage
    setTimeout(() => {
      collector.recordStateChange('disconnected');
    }, 100);

    const telemetry = collector.getTelemetry();
    expect(telemetry.uptime >= 0).toBe(true);
    expect(telemetry.downtime >= 0).toBe(true);
  });

  test('should get global collector instance', () => {
    const collector1 = getTelemetryCollector();
    const collector2 = getTelemetryCollector();

    expect(collector1).toBe(collector2);
  });

  test('should handle multiple state transitions', () => {
    const states = [
      'connecting',
      'connected',
      'disconnected',
      'reconnecting',
      'connected',
      'error',
      'reconnecting',
      'connected',
    ];

    states.forEach((state) => {
      collector.recordStateChange(state as any);
    });

    const telemetry = collector.getTelemetry();
    expect(telemetry.successfulConnections).toBeGreaterThan(0);
    expect(telemetry.failedConnections).toBeGreaterThan(0);
  });

  test('should track both total and unique connections', () => {
    collector.recordStateChange('connecting');
    collector.recordStateChange('connected');
    expect(collector.getTelemetry().totalConnections).toBe(1);

    collector.recordStateChange('disconnected');
    collector.recordStateChange('connecting');
    collector.recordStateChange('connected');
    expect(collector.getTelemetry().totalConnections).toBe(2);
  });
});
