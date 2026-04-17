/**
 * Hook for managing real-time alerts with WebSocket integration.
 */

import { useEffect, useState, useCallback } from 'react';
import { Alert, AlertSeverity, getAlertManager } from '../services/alertManager';
import { useRealtimeSubscription } from './useRealtimeSubscription';
import { MetricsEvent } from '../services/websocket';

interface UseAlertsReturn {
  alerts: Alert[];
  unreadAlerts: Alert[];
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  unreadCount: number;
  markAsRead: (alertId: string) => void;
  markAllAsRead: () => void;
  dismissAlert: (alertId: string) => void;
  dismissAllAlerts: () => void;
  getAlertsBySeverity: (severity: AlertSeverity) => Alert[];
}

export function useAlerts(userId: string): UseAlertsReturn {
  const alertManager = getAlertManager();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [, setUpdateTrigger] = useState(0);

  // Subscribe to alert events
  useRealtimeSubscription(
    'alert',
    userId,
    (event: MetricsEvent) => {
      try {
        alertManager.addAlert(event);
        setUpdateTrigger((prev) => prev + 1);
      } catch (error) {
        console.error('Failed to add alert:', error);
      }
      return null;
    }
  );

  // Update local state when alerts change
  useEffect(() => {
    const unsubscribe = alertManager.subscribe(() => {
      setAlerts(alertManager.getAlerts());
    });

    // Set initial state
    setAlerts(alertManager.getAlerts());

    return () => {
      unsubscribe();
    };
  }, []);

  const markAsRead = useCallback((alertId: string) => {
    alertManager.markAsRead(alertId);
    setUpdateTrigger((prev) => prev + 1);
  }, []);

  const markAllAsRead = useCallback(() => {
    alertManager.markAllAsRead();
    setUpdateTrigger((prev) => prev + 1);
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    alertManager.dismissAlert(alertId);
    setAlerts(alertManager.getAlerts());
  }, []);

  const dismissAllAlerts = useCallback(() => {
    alertManager.dismissAllAlerts();
    setAlerts([]);
  }, []);

  const getAlertsBySeverity = useCallback(
    (severity: AlertSeverity) => alertManager.getAlertsBySeverity(severity),
    []
  );

  return {
    alerts,
    unreadAlerts: alertManager.getUnreadAlerts(),
    criticalCount: alertManager.getCriticalCount(),
    warningCount: alertManager.getWarningCount(),
    infoCount: alertManager.getInfoCount(),
    unreadCount: alertManager.getUnreadCount(),
    markAsRead,
    markAllAsRead,
    dismissAlert,
    dismissAllAlerts,
    getAlertsBySeverity,
  };
}
