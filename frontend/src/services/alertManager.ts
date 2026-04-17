/**
 * Front-end alert manager for subscribing to and managing real-time alerts.
 */

import { MetricsEvent } from './websocket';

export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  triggerType: string;
  triggerValue: number;
  threshold: number;
  timestamp: Date;
  read: boolean;
}

export type AlertListener = (alert: Alert) => void;

export class AlertManager {
  private alerts: Map<string, Alert> = new Map();
  private listeners: Set<AlertListener> = new Set();
  private maxAlerts = 100;

  subscribe(listener: AlertListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  addAlert(event: MetricsEvent): Alert {
    if (event.type !== 'alert' || !event.data) {
      throw new Error('Invalid alert event');
    }

    const alert: Alert = {
      id: event.data.alert_id || `alert-${Date.now()}-${Math.random()}`,
      severity: event.data.level as AlertSeverity,
      title: event.data.title,
      message: event.data.message,
      triggerType: event.data.trigger_type || 'unknown',
      triggerValue: event.data.trigger_value || 0,
      threshold: event.data.threshold || 0,
      timestamp: new Date(event.timestamp),
      read: false,
    };

    this.alerts.set(alert.id, alert);

    // Maintain max size
    if (this.alerts.size > this.maxAlerts) {
      const firstKey = this.alerts.keys().next().value;
      if (firstKey) {
        this.alerts.delete(firstKey);
      }
    }

    // Notify listeners
    this.listeners.forEach((listener) => listener(alert));

    return alert;
  }

  getAlerts(): Alert[] {
    return Array.from(this.alerts.values()).sort(
      (a, b) => b.timestamp.getTime() - a.timestamp.getTime()
    );
  }

  getUnreadAlerts(): Alert[] {
    return this.getAlerts().filter((a) => !a.read);
  }

  getAlertsByTriggerType(triggerType: string): Alert[] {
    return this.getAlerts().filter((a) => a.triggerType === triggerType);
  }

  getAlertsBySeverity(severity: AlertSeverity): Alert[] {
    return this.getAlerts().filter((a) => a.severity === severity);
  }

  markAsRead(alertId: string): void {
    const alert = this.alerts.get(alertId);
    if (alert) {
      alert.read = true;
    }
  }

  markAllAsRead(): void {
    this.alerts.forEach((alert) => {
      alert.read = true;
    });
  }

  dismissAlert(alertId: string): void {
    this.alerts.delete(alertId);
  }

  dismissAllAlerts(): void {
    this.alerts.clear();
  }

  getCriticalCount(): number {
    return this.getAlertsBySeverity('critical').length;
  }

  getWarningCount(): number {
    return this.getAlertsBySeverity('warning').length;
  }

  getInfoCount(): number {
    return this.getAlertsBySeverity('info').length;
  }

  getUnreadCount(): number {
    return this.getUnreadAlerts().length;
  }

  clear(): void {
    this.alerts.clear();
    this.listeners.clear();
  }
}

// Global instance
let globalAlertManager: AlertManager | null = null;

export function getAlertManager(): AlertManager {
  if (!globalAlertManager) {
    globalAlertManager = new AlertManager();
  }
  return globalAlertManager;
}

export function createAlertManager(): AlertManager {
  return new AlertManager();
}
