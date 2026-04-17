/**
 * Tests for alert manager service.
 */

import { AlertManager, getAlertManager, createAlertManager } from '../src/services/alertManager';
import { MetricsEvent } from '../src/services/websocket';

describe('AlertManager', () => {
  let manager: AlertManager;

  beforeEach(() => {
    manager = createAlertManager();
  });

  test('should create alert from event', () => {
    const event: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-1',
        level: 'warning',
        title: 'Test Alert',
        message: 'Test message',
        trigger_type: 'high_cost',
        trigger_value: 15.0,
        threshold: 10.0,
      },
    };

    const alert = manager.addAlert(event);

    expect(alert.id).toBe('alert-1');
    expect(alert.severity).toBe('warning');
    expect(alert.title).toBe('Test Alert');
  });

  test('should generate ID if not provided', () => {
    const event: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        level: 'info',
        title: 'Auto ID Alert',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    const alert = manager.addAlert(event);
    expect(alert.id).toBeDefined();
    expect(alert.id).toContain('alert-');
  });

  test('should get all alerts sorted by newest first', () => {
    const now = new Date();

    for (let i = 0; i < 3; i++) {
      const event: MetricsEvent = {
        type: 'alert',
        timestamp: new Date(now.getTime() + i * 1000).toISOString(),
        data: {
          alert_id: `alert-${i}`,
          level: 'info',
          title: `Alert ${i}`,
          message: 'Test',
          trigger_type: 'test',
          trigger_value: 0,
          threshold: 0,
        },
      };
      manager.addAlert(event);
    }

    const alerts = manager.getAlerts();
    expect(alerts.length).toBe(3);
    expect(alerts[0].id).toBe('alert-2');
  });

  test('should get unread alerts', () => {
    const event: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-1',
        level: 'info',
        title: 'Unread Alert',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    manager.addAlert(event);
    let unread = manager.getUnreadAlerts();
    expect(unread.length).toBe(1);

    manager.markAsRead('alert-1');
    unread = manager.getUnreadAlerts();
    expect(unread.length).toBe(0);
  });

  test('should filter alerts by trigger type', () => {
    const event1: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-1',
        level: 'info',
        title: 'Alert 1',
        message: 'Test',
        trigger_type: 'high_cost',
        trigger_value: 0,
        threshold: 0,
      },
    };

    const event2: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-2',
        level: 'info',
        title: 'Alert 2',
        message: 'Test',
        trigger_type: 'slow_query',
        trigger_value: 0,
        threshold: 0,
      },
    };

    manager.addAlert(event1);
    manager.addAlert(event2);

    const highCostAlerts = manager.getAlertsByTriggerType('high_cost');
    expect(highCostAlerts.length).toBe(1);
    expect(highCostAlerts[0].id).toBe('alert-1');
  });

  test('should filter alerts by severity', () => {
    const critical: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-critical',
        level: 'critical',
        title: 'Critical',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    const warning: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-warning',
        level: 'warning',
        title: 'Warning',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    manager.addAlert(critical);
    manager.addAlert(warning);

    const criticalAlerts = manager.getAlertsBySeverity('critical');
    expect(criticalAlerts.length).toBe(1);
    expect(criticalAlerts[0].id).toBe('alert-critical');
  });

  test('should mark alert as read', () => {
    const event: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-1',
        level: 'info',
        title: 'Test',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    manager.addAlert(event);
    manager.markAsRead('alert-1');

    const alerts = manager.getAlerts();
    expect(alerts[0].read).toBe(true);
  });

  test('should mark all alerts as read', () => {
    for (let i = 0; i < 3; i++) {
      const event: MetricsEvent = {
        type: 'alert',
        timestamp: new Date().toISOString(),
        data: {
          alert_id: `alert-${i}`,
          level: 'info',
          title: `Alert ${i}`,
          message: 'Test',
          trigger_type: 'test',
          trigger_value: 0,
          threshold: 0,
        },
      };
      manager.addAlert(event);
    }

    manager.markAllAsRead();

    const alerts = manager.getAlerts();
    expect(alerts.every((a) => a.read)).toBe(true);
  });

  test('should dismiss alert', () => {
    const event: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-1',
        level: 'info',
        title: 'Test',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    manager.addAlert(event);
    expect(manager.getAlerts().length).toBe(1);

    manager.dismissAlert('alert-1');
    expect(manager.getAlerts().length).toBe(0);
  });

  test('should dismiss all alerts', () => {
    for (let i = 0; i < 3; i++) {
      const event: MetricsEvent = {
        type: 'alert',
        timestamp: new Date().toISOString(),
        data: {
          alert_id: `alert-${i}`,
          level: 'info',
          title: `Alert ${i}`,
          message: 'Test',
          trigger_type: 'test',
          trigger_value: 0,
          threshold: 0,
        },
      };
      manager.addAlert(event);
    }

    expect(manager.getAlerts().length).toBe(3);
    manager.dismissAllAlerts();
    expect(manager.getAlerts().length).toBe(0);
  });

  test('should get severity counts', () => {
    const severities = ['critical', 'warning', 'info'];

    severities.forEach((severity) => {
      const event: MetricsEvent = {
        type: 'alert',
        timestamp: new Date().toISOString(),
        data: {
          alert_id: `alert-${severity}`,
          level: severity,
          title: 'Test',
          message: 'Test',
          trigger_type: 'test',
          trigger_value: 0,
          threshold: 0,
        },
      };
      manager.addAlert(event);
    });

    expect(manager.getCriticalCount()).toBe(1);
    expect(manager.getWarningCount()).toBe(1);
    expect(manager.getInfoCount()).toBe(1);
  });

  test('should get unread count', () => {
    for (let i = 0; i < 3; i++) {
      const event: MetricsEvent = {
        type: 'alert',
        timestamp: new Date().toISOString(),
        data: {
          alert_id: `alert-${i}`,
          level: 'info',
          title: 'Test',
          message: 'Test',
          trigger_type: 'test',
          trigger_value: 0,
          threshold: 0,
        },
      };
      manager.addAlert(event);
    }

    expect(manager.getUnreadCount()).toBe(3);

    manager.markAsRead('alert-0');
    expect(manager.getUnreadCount()).toBe(2);

    manager.markAllAsRead();
    expect(manager.getUnreadCount()).toBe(0);
  });

  test('should respect max alerts limit', () => {
    const manager = createAlertManager();

    for (let i = 0; i < 150; i++) {
      const event: MetricsEvent = {
        type: 'alert',
        timestamp: new Date().toISOString(),
        data: {
          alert_id: `alert-${i}`,
          level: 'info',
          title: 'Test',
          message: 'Test',
          trigger_type: 'test',
          trigger_value: 0,
          threshold: 0,
        },
      };
      manager.addAlert(event);
    }

    expect(manager.getAlerts().length).toBeLessThanOrEqual(100);
  });

  test('should support alert listeners', () => {
    const listener = jest.fn();
    const unsubscribe = manager.subscribe(listener);

    const event: MetricsEvent = {
      type: 'alert',
      timestamp: new Date().toISOString(),
      data: {
        alert_id: 'alert-1',
        level: 'info',
        title: 'Test',
        message: 'Test',
        trigger_type: 'test',
        trigger_value: 0,
        threshold: 0,
      },
    };

    manager.addAlert(event);
    expect(listener).toHaveBeenCalled();

    unsubscribe();
    manager.addAlert(event);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  test('should get global alert manager', () => {
    const manager1 = getAlertManager();
    const manager2 = getAlertManager();

    expect(manager1).toBe(manager2);
  });

  test('should handle invalid alert event', () => {
    const invalidEvent: MetricsEvent = {
      type: 'query_update',
      timestamp: new Date().toISOString(),
      data: {},
    };

    expect(() => manager.addAlert(invalidEvent)).toThrow();
  });
});
