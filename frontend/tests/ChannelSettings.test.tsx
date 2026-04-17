/**
 * Tests for ChannelSettings component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChannelSettings, ChannelConfig } from '../src/components/ChannelSettings';

describe('ChannelSettings', () => {
  const mockChannels: ChannelConfig[] = [
    {
      id: 'email-1',
      type: 'email',
      destination: 'alerts@example.com',
      enabled: true,
      includeCritical: true,
      includeWarning: true,
      includeInfo: false,
    },
    {
      id: 'slack-1',
      type: 'slack',
      destination: 'https://hooks.slack.com/...',
      enabled: true,
      includeCritical: true,
      includeWarning: false,
      includeInfo: false,
    },
  ];

  test('should render channel list', () => {
    render(
      <ChannelSettings channels={mockChannels} />
    );

    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Slack')).toBeInTheDocument();
  });

  test('should display channel destinations', () => {
    render(
      <ChannelSettings channels={mockChannels} />
    );

    expect(screen.getByText('alerts@example.com')).toBeInTheDocument();
    expect(screen.getByText('https://hooks.slack.com/...')).toBeInTheDocument();
  });

  test('should show severity checkboxes for each channel', () => {
    render(
      <ChannelSettings channels={mockChannels} />
    );

    const criticals = screen.getAllByText('Critical');
    const warnings = screen.getAllByText('Warning');

    expect(criticals.length).toBeGreaterThan(0);
    expect(warnings.length).toBeGreaterThan(0);
  });

  test('should call onAddChannel when adding new channel', () => {
    const onAddChannel = jest.fn();
    const { container } = render(
      <ChannelSettings channels={mockChannels} onAddChannel={onAddChannel} />
    );

    const addButton = screen.getByText('+ Add Channel');
    fireEvent.click(addButton);

    const typeSelect = container.querySelector('select');
    const input = container.querySelector('input[type="text"]') as HTMLInputElement;

    fireEvent.change(typeSelect!, { target: { value: 'email' } });
    fireEvent.change(input, { target: { value: 'newuser@example.com' } });

    const submitButton = screen.getByText('Add Channel');
    fireEvent.click(submitButton);

    expect(onAddChannel).toHaveBeenCalled();
  });

  test('should call onRemoveChannel when removing channel', () => {
    const onRemoveChannel = jest.fn();
    render(
      <ChannelSettings
        channels={mockChannels}
        onRemoveChannel={onRemoveChannel}
      />
    );

    const removeButtons = screen.getAllByText('Remove');
    fireEvent.click(removeButtons[0]);

    expect(onRemoveChannel).toHaveBeenCalledWith('email-1');
  });

  test('should toggle channel enabled state', () => {
    const onUpdateChannel = jest.fn();
    const { container } = render(
      <ChannelSettings
        channels={mockChannels}
        onUpdateChannel={onUpdateChannel}
      />
    );

    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    fireEvent.click(checkboxes[0]);

    expect(onUpdateChannel).toHaveBeenCalled();
  });

  test('should call onTestChannel when sending test', async () => {
    const onTestChannel = jest.fn().mockResolvedValue(true);
    render(
      <ChannelSettings
        channels={mockChannels}
        onTestChannel={onTestChannel}
      />
    );

    const testButtons = screen.getAllByText('Send Test');
    fireEvent.click(testButtons[0]);

    await waitFor(() => {
      expect(onTestChannel).toHaveBeenCalled();
    });
  });

  test('should show test result message', async () => {
    const onTestChannel = jest.fn().mockResolvedValue(true);
    render(
      <ChannelSettings
        channels={mockChannels}
        onTestChannel={onTestChannel}
      />
    );

    const testButtons = screen.getAllByText('Send Test');
    fireEvent.click(testButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('✓ Test succeeded')).toBeInTheDocument();
    });
  });

  test('should disable add when destination empty', () => {
    render(
      <ChannelSettings channels={mockChannels} />
    );

    fireEvent.click(screen.getByText('+ Add Channel'));

    const addButton = screen.getByText('Add Channel');
    expect(addButton).toBeDisabled();
  });

  test('should show form hints for each channel type', () => {
    const { container, rerender } = render(
      <ChannelSettings channels={[]} />
    );

    fireEvent.click(screen.getByText('+ Add Channel'));

    const select = container.querySelector('select') as HTMLSelectElement;

    fireEvent.change(select, { target: { value: 'email' } });
    expect(screen.getByText('Enter email address')).toBeInTheDocument();

    rerender(<ChannelSettings channels={[]} />);
    fireEvent.click(screen.getByText('+ Add Channel'));

    fireEvent.change(select, { target: { value: 'slack' } });
    expect(screen.getByText('Paste your Slack webhook URL')).toBeInTheDocument();
  });
});
