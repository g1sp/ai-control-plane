/**
 * Tests for AlertCenter component.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AlertCenter, Alert } from '../src/components/AlertCenter';

describe('AlertCenter', () => {
  const mockAlert: Alert = {
    id: 'alert-1',
    severity: 'info',
    title: 'Test Alert',
    message: 'This is a test alert',
    timestamp: new Date(),
  };

  test('should render nothing when no alerts', () => {
    const { container } = render(<AlertCenter alerts={[]} />);
    expect(container.firstChild).toBeNull();
  });

  test('should render alerts', () => {
    render(<AlertCenter alerts={[mockAlert]} />);
    expect(screen.getByText('Test Alert')).toBeInTheDocument();
    expect(screen.getByText('This is a test alert')).toBeInTheDocument();
  });

  test('should display critical alert styling', () => {
    const criticalAlert: Alert = {
      ...mockAlert,
      id: 'alert-critical',
      severity: 'critical',
    };

    render(<AlertCenter alerts={[criticalAlert]} />);
    const alertElement = screen.getByText('Test Alert').closest('div');
    expect(alertElement).toHaveClass('text-red-900');
  });

  test('should display warning alert styling', () => {
    const warningAlert: Alert = {
      ...mockAlert,
      id: 'alert-warning',
      severity: 'warning',
    };

    render(<AlertCenter alerts={[warningAlert]} />);
    const alertElement = screen.getByText('Test Alert').closest('div');
    expect(alertElement).toHaveClass('text-yellow-900');
  });

  test('should display info alert styling', () => {
    const infoAlert: Alert = {
      ...mockAlert,
      id: 'alert-info',
      severity: 'info',
    };

    render(<AlertCenter alerts={[infoAlert]} />);
    const alertElement = screen.getByText('Test Alert').closest('div');
    expect(alertElement).toHaveClass('text-blue-900');
  });

  test('should display severity badges', () => {
    render(<AlertCenter alerts={[mockAlert]} />);
    expect(screen.getByText('INFO')).toBeInTheDocument();
  });

  test('should display timestamp', () => {
    const now = new Date();
    const alert: Alert = {
      ...mockAlert,
      timestamp: now,
    };

    render(<AlertCenter alerts={[alert]} />);
    const timeString = now.toLocaleTimeString();
    expect(screen.getByText(timeString)).toBeInTheDocument();
  });

  test('should dismiss alert on button click', () => {
    const { container } = render(<AlertCenter alerts={[mockAlert]} />);
    const dismissButton = container.querySelector('button');

    fireEvent.click(dismissButton!);

    expect(screen.queryByText('Test Alert')).not.toBeInTheDocument();
  });

  test('should call onDismiss callback when alert dismissed', () => {
    const onDismiss = jest.fn();
    const { container } = render(
      <AlertCenter alerts={[mockAlert]} onDismiss={onDismiss} />
    );

    const dismissButton = container.querySelector('button');
    fireEvent.click(dismissButton!);

    expect(onDismiss).toHaveBeenCalledWith('alert-1');
  });

  test('should hide dismiss button when dismissable is false', () => {
    const nonDismissableAlert: Alert = {
      ...mockAlert,
      dismissable: false,
    };

    const { container } = render(<AlertCenter alerts={[nonDismissableAlert]} />);
    expect(container.querySelector('button')).not.toBeInTheDocument();
  });

  test('should respect maxVisible limit', () => {
    const alerts: Alert[] = Array.from({ length: 10 }, (_, i) => ({
      ...mockAlert,
      id: `alert-${i}`,
      title: `Alert ${i}`,
    }));

    render(<AlertCenter alerts={alerts} maxVisible={3} />);

    expect(screen.getByText('Alert 0')).toBeInTheDocument();
    expect(screen.getByText('Alert 1')).toBeInTheDocument();
    expect(screen.getByText('Alert 2')).toBeInTheDocument();
    expect(screen.queryByText('Alert 3')).not.toBeInTheDocument();
  });

  test('should display count of hidden alerts', () => {
    const alerts: Alert[] = Array.from({ length: 8 }, (_, i) => ({
      ...mockAlert,
      id: `alert-${i}`,
      title: `Alert ${i}`,
    }));

    render(<AlertCenter alerts={alerts} maxVisible={3} />);

    expect(screen.getByText('+5 more alerts')).toBeInTheDocument();
  });

  test('should handle multiple alerts of different severities', () => {
    const alerts: Alert[] = [
      { ...mockAlert, id: 'alert-1', severity: 'info', title: 'Info Alert' },
      { ...mockAlert, id: 'alert-2', severity: 'warning', title: 'Warning Alert' },
      { ...mockAlert, id: 'alert-3', severity: 'critical', title: 'Critical Alert' },
    ];

    render(<AlertCenter alerts={alerts} />);

    expect(screen.getByText('INFO')).toBeInTheDocument();
    expect(screen.getByText('WARNING')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  test('should update when new alert added', () => {
    const { rerender } = render(<AlertCenter alerts={[mockAlert]} />);

    const newAlert: Alert = {
      id: 'alert-2',
      severity: 'critical',
      title: 'New Alert',
      message: 'New alert message',
      timestamp: new Date(),
    };

    rerender(<AlertCenter alerts={[mockAlert, newAlert]} />);

    expect(screen.getByText('Test Alert')).toBeInTheDocument();
    expect(screen.getByText('New Alert')).toBeInTheDocument();
  });

  test('should remove dismissed alert from display', () => {
    const alerts: Alert[] = [
      { ...mockAlert, id: 'alert-1', title: 'Alert 1' },
      { ...mockAlert, id: 'alert-2', title: 'Alert 2' },
    ];

    const onDismiss = jest.fn();
    const { container, rerender } = render(
      <AlertCenter alerts={alerts} onDismiss={onDismiss} />
    );

    const dismissButtons = container.querySelectorAll('button');
    fireEvent.click(dismissButtons[0]);

    expect(screen.queryByText('Alert 1')).not.toBeInTheDocument();
    expect(screen.getByText('Alert 2')).toBeInTheDocument();
  });
});
