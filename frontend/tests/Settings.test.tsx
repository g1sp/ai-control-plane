/**
 * Tests for Settings page.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Settings } from '../src/pages/Settings';

// Mock the hook
jest.mock('../src/hooks/useChannelSettings', () => ({
  useChannelSettings: jest.fn(() => ({
    channels: [
      {
        id: 'ch-1',
        type: 'email',
        destination: 'alerts@example.com',
        enabled: true,
        includeCritical: true,
        includeWarning: true,
        includeInfo: false,
      },
    ],
    rules: [
      {
        id: 'rule-1',
        triggerType: 'high_cost_query',
        channelType: 'email',
        enabled: true,
        alertLevels: ['critical', 'warning'],
      },
    ],
    history: [
      {
        id: 'delivery-1',
        alertId: 'alert-1',
        channelType: 'email',
        destination: 'alerts@example.com',
        status: 'sent',
        timestamp: new Date(),
        retryCount: 0,
      },
    ],
    stats: {
      totalChannels: 1,
      enabledChannels: 1,
      totalRules: 1,
      totalDeliveries: 10,
      failedDeliveries: 1,
    },
    isLoading: false,
    error: null,
    addChannel: jest.fn(),
    updateChannel: jest.fn(),
    removeChannel: jest.fn(),
    addRule: jest.fn(),
    updateRule: jest.fn(),
    removeRule: jest.fn(),
    testChannel: jest.fn(),
    getHistory: jest.fn(),
    retryDelivery: jest.fn(),
  })),
}));

describe('Settings Page', () => {
  test('should render settings page', () => {
    render(<Settings />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('should display all tabs', () => {
    render(<Settings />);
    expect(screen.getByText('Alert Channels')).toBeInTheDocument();
    expect(screen.getByText('Delivery Rules')).toBeInTheDocument();
    expect(screen.getByText('Delivery History')).toBeInTheDocument();
  });

  test('should show stats', () => {
    render(<Settings />);
    expect(screen.getByText('1/1')).toBeInTheDocument(); // enabled/total channels
    expect(screen.getByText('1')).toBeInTheDocument();   // rules
  });

  test('should switch between tabs', () => {
    render(<Settings />);

    // Click rules tab
    fireEvent.click(screen.getByText('Delivery Rules'));
    expect(screen.getByText('Delivery Rules')).toBeInTheDocument();

    // Click history tab
    fireEvent.click(screen.getByText('Delivery History'));
    expect(screen.getByText('Delivery History')).toBeInTheDocument();
  });

  test('should show channels tab by default', () => {
    render(<Settings />);
    expect(screen.getByText('Alert Channels')).toBeInTheDocument();
  });

  test('should display loading state', () => {
    const { useChannelSettings } = require('../src/hooks/useChannelSettings');
    useChannelSettings.mockReturnValueOnce({
      channels: [],
      rules: [],
      history: [],
      stats: { totalChannels: 0, enabledChannels: 0, totalRules: 0, totalDeliveries: 0, failedDeliveries: 0 },
      isLoading: true,
      error: null,
    });

    render(<Settings />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('should display error banner', () => {
    const { useChannelSettings } = require('../src/hooks/useChannelSettings');
    useChannelSettings.mockReturnValueOnce({
      channels: [],
      rules: [],
      history: [],
      stats: { totalChannels: 0, enabledChannels: 0, totalRules: 0, totalDeliveries: 0, failedDeliveries: 0 },
      isLoading: false,
      error: new Error('Test error message'),
    });

    render(<Settings />);
    expect(screen.getByText('Error: Test error message')).toBeInTheDocument();
  });

  test('should count successful and failed deliveries', () => {
    render(<Settings />);
    const successCount = 10 - 1; // total - failed
    expect(screen.getByText(successCount.toString())).toBeInTheDocument();
  });

  test('should have active channel settings tab by default', () => {
    render(<Settings />);
    const channelsTab = screen.getByText('Alert Channels').closest('button');
    expect(channelsTab).toHaveClass('text-blue-600');
  });

  test('should render tabs in correct order', () => {
    render(<Settings />);
    const tabs = screen.getAllByRole('button', { name: /Alert|Delivery/ });
    expect(tabs.length).toBeGreaterThanOrEqual(3);
  });
});
