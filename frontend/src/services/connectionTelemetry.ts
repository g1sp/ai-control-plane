/**
 * Telemetry collection for WebSocket connection quality metrics.
 */

import { ConnectionState } from './websocket';

export interface ConnectionTelemetry {
  totalConnections: number;
  successfulConnections: number;
  failedConnections: number;
  reconnectionAttempts: number;
  totalMessagesSent: number;
  totalMessagesReceived: number;
  averageLatency: number;
  maxLatency: number;
  minLatency: number;
  uptime: number; // milliseconds
  downtime: number; // milliseconds
  averageReconnectionTime: number; // milliseconds
  lastConnectionTime: Date | null;
  lastDisconnectionTime: Date | null;
  connectionErrors: string[];
}

interface ConnectionMetric {
  timestamp: Date;
  state: ConnectionState;
  latency?: number;
  error?: string;
}

export class ConnectionTelemetryCollector {
  private metrics: ConnectionMetric[] = [];
  private maxMetrics = 1000;

  private totalConnections = 0;
  private successfulConnections = 0;
  private failedConnections = 0;
  private reconnectionAttempts = 0;
  private totalMessagesSent = 0;
  private totalMessagesReceived = 0;
  private latencies: number[] = [];
  private connectionErrors: string[] = [];
  private maxErrors = 100;

  private connectTime: Date | null = null;
  private disconnectTime: Date | null = null;
  private lastConnectionTime: Date | null = null;
  private lastDisconnectionTime: Date | null = null;
  private reconnectionTimes: number[] = [];

  recordStateChange(state: ConnectionState, error?: string): void {
    const metric: ConnectionMetric = {
      timestamp: new Date(),
      state,
      error,
    };

    this.metrics.push(metric);
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.shift();
    }

    if (state === 'connected') {
      this.successfulConnections++;
      this.totalConnections++;
      this.connectTime = new Date();
      this.lastConnectionTime = new Date();

      if (this.lastDisconnectionTime) {
        const reconnectionTime = this.connectTime.getTime() - this.lastDisconnectionTime.getTime();
        this.reconnectionTimes.push(reconnectionTime);
        if (this.reconnectionTimes.length > 100) {
          this.reconnectionTimes.shift();
        }
      }
    } else if (state === 'disconnected' || state === 'error') {
      this.disconnectTime = new Date();
      this.lastDisconnectionTime = new Date();

      if (state === 'error') {
        this.failedConnections++;
        if (error) {
          this.connectionErrors.push(`${new Date().toISOString()}: ${error}`);
          if (this.connectionErrors.length > this.maxErrors) {
            this.connectionErrors.shift();
          }
        }
      }
    } else if (state === 'reconnecting') {
      this.reconnectionAttempts++;
    }
  }

  recordMessageSent(): void {
    this.totalMessagesSent++;
  }

  recordMessageReceived(): void {
    this.totalMessagesReceived++;
  }

  recordLatency(latency: number): void {
    this.latencies.push(latency);
    if (this.latencies.length > 1000) {
      this.latencies.shift();
    }
  }

  getTelemetry(): ConnectionTelemetry {
    const avgLatency = this.latencies.length > 0
      ? this.latencies.reduce((a, b) => a + b, 0) / this.latencies.length
      : 0;

    const maxLatency = this.latencies.length > 0 ? Math.max(...this.latencies) : 0;
    const minLatency = this.latencies.length > 0 ? Math.min(...this.latencies) : 0;

    let uptime = 0;
    let downtime = 0;

    for (let i = 0; i < this.metrics.length - 1; i++) {
      const current = this.metrics[i];
      const next = this.metrics[i + 1];
      const duration = next.timestamp.getTime() - current.timestamp.getTime();

      if (current.state === 'connected') {
        uptime += duration;
      } else {
        downtime += duration;
      }
    }

    const avgReconnectionTime = this.reconnectionTimes.length > 0
      ? this.reconnectionTimes.reduce((a, b) => a + b, 0) / this.reconnectionTimes.length
      : 0;

    return {
      totalConnections: this.totalConnections,
      successfulConnections: this.successfulConnections,
      failedConnections: this.failedConnections,
      reconnectionAttempts: this.reconnectionAttempts,
      totalMessagesSent: this.totalMessagesSent,
      totalMessagesReceived: this.totalMessagesReceived,
      averageLatency: avgLatency,
      maxLatency,
      minLatency,
      uptime,
      downtime,
      averageReconnectionTime: avgReconnectionTime,
      lastConnectionTime: this.lastConnectionTime,
      lastDisconnectionTime: this.lastDisconnectionTime,
      connectionErrors: this.connectionErrors,
    };
  }

  reset(): void {
    this.metrics = [];
    this.totalConnections = 0;
    this.successfulConnections = 0;
    this.failedConnections = 0;
    this.reconnectionAttempts = 0;
    this.totalMessagesSent = 0;
    this.totalMessagesReceived = 0;
    this.latencies = [];
    this.connectionErrors = [];
    this.connectTime = null;
    this.disconnectTime = null;
    this.lastConnectionTime = null;
    this.lastDisconnectionTime = null;
    this.reconnectionTimes = [];
  }

  getMetricsHistory(limit: number = 100): ConnectionMetric[] {
    return this.metrics.slice(-limit);
  }
}

// Global instance
let globalCollector: ConnectionTelemetryCollector | null = null;

export function getTelemetryCollector(): ConnectionTelemetryCollector {
  if (!globalCollector) {
    globalCollector = new ConnectionTelemetryCollector();
  }
  return globalCollector;
}
