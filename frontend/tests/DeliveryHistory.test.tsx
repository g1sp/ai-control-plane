/**
 * Tests for DeliveryHistory component.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { DeliveryHistory } from '../src/components/DeliveryHistory';

describe('DeliveryHistory', () => {
  const mockRecords = [
    {
      id: 'delivery-1',
      alertId: 'alert-1',
      channelType: 'email',
      destination: 'alerts@example.com',
      status: 'sent' as const,
      timestamp: new Date(),
      retryCount: 0,
    },
    {
      id: 'delivery-2',
      alertId: 'alert-2',
      channelType: 'slack',
      destination: 'https://hooks.slack.com/...',
      status: 'failed' as const,
      timestamp: new Date(),
      errorMessage: 'Connection timeout',
      retryCount: 2,
    },
  ];

  test('should render delivery history', () => {
    render(<DeliveryHistory records={mockRecords} />);
    expect(screen.getByText('Delivery History')).toBeInTheDocument();
  });

  test('should display delivery records', () => {
    render(<DeliveryHistory records={mockRecords} />);
    expect(screen.getByText('email')).toBeInTheDocument();
    expect(screen.getByText('slack')).toBeInTheDocument();
  });

  test('should show status filters', () => {
    render(<DeliveryHistory records={mockRecords} />);
    expect(screen.getByText('All (2)')).toBeInTheDocument();
    expect(screen.getByText('Pending (0)')).toBeInTheDocument();
    expect(screen.getByText('Sent (1)')).toBeInTheDocument();
    expect(screen.getByText('Failed (1)')).toBeInTheDocument();
  });

  test('should filter by status', () => {
    render(<DeliveryHistory records={mockRecords} />);

    fireEvent.click(screen.getByText('Sent (1)'));
    expect(screen.getByText('Sent')).toBeInTheDocument();
    expect(screen.queryByText('slack')).not.toBeInTheDocument();
  });

  test('should expand record for details', () => {
    render(<DeliveryHistory records={mockRecords} />);

    const emailRecord = screen.getByText('email').closest('div');
    fireEvent.click(emailRecord!);

    expect(screen.getByText('alert-1')).toBeInTheDocument();
    expect(screen.getByText('0/3')).toBeInTheDocument(); // retries
  });

  test('should show error message for failed delivery', () => {
    render(<DeliveryHistory records={mockRecords} />);

    const failedRecord = screen.getByText('slack').closest('div');
    fireEvent.click(failedRecord!);

    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  test('should display retry button for failed deliveries', () => {
    render(<DeliveryHistory records={mockRecords} />);

    const failedRecord = screen.getByText('slack').closest('div');
    fireEvent.click(failedRecord!);

    expect(screen.getByText('Retry Delivery')).toBeInTheDocument();
  });

  test('should call onRetry when clicking retry button', () => {
    const onRetry = jest.fn();
    render(<DeliveryHistory records={mockRecords} onRetry={onRetry} />);

    const failedRecord = screen.getByText('slack').closest('div');
    fireEvent.click(failedRecord!);

    const retryButton = screen.getByText('Retry Delivery');
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalledWith('delivery-2');
  });

  test('should show summary statistics', () => {
    render(<DeliveryHistory records={mockRecords} />);

    expect(screen.getByText('1')).toBeInTheDocument(); // successful
    expect(screen.getByText('Successful')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  test('should display retry count', () => {
    render(<DeliveryHistory records={mockRecords} />);

    const failedRecord = screen.getByText('slack').closest('div');
    fireEvent.click(failedRecord!);

    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  test('should show no message when no records', () => {
    render(<DeliveryHistory records={[]} />);
    expect(screen.getByText('No delivery records found')).toBeInTheDocument();
  });

  test('should collapse expanded record when clicking again', () => {
    render(<DeliveryHistory records={mockRecords} />);

    const emailRecord = screen.getByText('email').closest('div');
    fireEvent.click(emailRecord!);
    expect(screen.getByText('alert-1')).toBeInTheDocument();

    fireEvent.click(emailRecord!);
    expect(screen.queryByText('alert-1')).not.toBeInTheDocument();
  });

  test('should display timestamp for each record', () => {
    render(<DeliveryHistory records={mockRecords} />);

    const records = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/);
    expect(records.length).toBeGreaterThan(0);
  });

  test('should show delivery destination', () => {
    render(<DeliveryHistory records={mockRecords} />);

    expect(screen.getByText('alerts@example.com')).toBeInTheDocument();
    expect(screen.getByText('https://hooks.slack.com/...')).toBeInTheDocument();
  });

  test('should handle multiple status filters', () => {
    const manyRecords = [
      ...mockRecords,
      {
        id: 'delivery-3',
        alertId: 'alert-3',
        channelType: 'pagerduty',
        destination: 'integration-key',
        status: 'pending' as const,
        timestamp: new Date(),
        retryCount: 0,
      },
    ];

    render(<DeliveryHistory records={manyRecords} />);

    expect(screen.getByText('Pending (1)')).toBeInTheDocument();
  });

  test('should not show retry button when max retries exceeded', () => {
    const maxRetriesRecord = [
      {
        id: 'delivery-max',
        alertId: 'alert-max',
        channelType: 'email',
        destination: 'test@example.com',
        status: 'failed' as const,
        timestamp: new Date(),
        retryCount: 3,
      },
    ];

    render(<DeliveryHistory records={maxRetriesRecord} />);

    const record = screen.getByText('email').closest('div');
    fireEvent.click(record!);

    expect(screen.queryByText('Retry Delivery')).not.toBeInTheDocument();
  });
});
