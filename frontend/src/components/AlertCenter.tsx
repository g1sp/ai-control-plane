/**
 * Component for managing and displaying real-time alerts.
 */

import React, { useState, useCallback } from 'react';

export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  timestamp: Date;
  dismissable?: boolean;
}

interface AlertCenterProps {
  alerts: Alert[];
  onDismiss?: (alertId: string) => void;
  maxVisible?: number;
}

export function AlertCenter({ alerts, onDismiss, maxVisible = 5 }: AlertCenterProps) {
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  const visibleAlerts = alerts
    .filter((alert) => !dismissedAlerts.has(alert.id))
    .slice(0, maxVisible);

  const handleDismiss = useCallback(
    (alertId: string) => {
      setDismissedAlerts((prev) => new Set([...prev, alertId]));
      onDismiss?.(alertId);
    },
    [onDismiss]
  );

  const getSeverityColor = (severity: AlertSeverity): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-900';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-900';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200 text-blue-900';
    }
  };

  const getSeverityBadge = (severity: AlertSeverity): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-200 text-yellow-800';
      case 'info':
      default:
        return 'bg-blue-200 text-blue-800';
    }
  };

  if (visibleAlerts.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-20 right-4 space-y-2 z-50 max-w-md">
      {visibleAlerts.map((alert) => (
        <div
          key={alert.id}
          className={`border rounded-lg p-4 shadow-md ${getSeverityColor(alert.severity)}`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityBadge(alert.severity)}`}>
                {alert.severity.toUpperCase()}
              </span>
              <div className="flex-1">
                <h4 className="font-semibold text-sm">{alert.title}</h4>
                <p className="text-sm mt-1">{alert.message}</p>
                <span className="text-xs opacity-75 mt-1 block">
                  {alert.timestamp.toLocaleTimeString()}
                </span>
              </div>
            </div>
            {alert.dismissable !== false && (
              <button
                onClick={() => handleDismiss(alert.id)}
                className="ml-2 text-lg opacity-50 hover:opacity-100 transition"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      ))}
      {alerts.length > maxVisible && (
        <div className="text-center text-xs text-gray-500 mt-2">
          +{alerts.length - maxVisible} more alerts
        </div>
      )}
    </div>
  );
}
