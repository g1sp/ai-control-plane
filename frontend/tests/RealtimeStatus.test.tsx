/**
 * Tests for RealtimeStatus component.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { RealtimeStatus } from '../src/components/RealtimeStatus';

describe('RealtimeStatus', () => {
  test('should display connected status', () => {
    render(
      <RealtimeStatus
        connectionState="connected"
        lastUpdateTime={new Date()}
      />
    );

    expect(screen.getByText('●')).toBeInTheDocument();
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  test('should display connecting status', () => {
    render(
      <RealtimeStatus
        connectionState="connecting"
        lastUpdateTime={null}
      />
    );

    expect(screen.getByText('◌')).toBeInTheDocument();
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  test('should display reconnecting status', () => {
    render(
      <RealtimeStatus
        connectionState="reconnecting"
        lastUpdateTime={null}
      />
    );

    expect(screen.getByText('◌')).toBeInTheDocument();
    expect(screen.getByText('Reconnecting...')).toBeInTheDocument();
  });

  test('should display error status', () => {
    render(
      <RealtimeStatus
        connectionState="error"
        lastUpdateTime={null}
      />
    );

    expect(screen.getByText('✕')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  test('should display disconnected status', () => {
    render(
      <RealtimeStatus
        connectionState="disconnected"
        lastUpdateTime={null}
      />
    );

    expect(screen.getByText('○')).toBeInTheDocument();
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  test('should display last update time when connected', () => {
    const now = new Date();
    render(
      <RealtimeStatus
        connectionState="connected"
        lastUpdateTime={now}
      />
    );

    expect(screen.getByText(/Updated \d+s ago/)).toBeInTheDocument();
  });

  test('should display correct colors for connected state', () => {
    const { container } = render(
      <RealtimeStatus
        connectionState="connected"
        lastUpdateTime={new Date()}
      />
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('text-green-600');
  });

  test('should display correct colors for reconnecting state', () => {
    const { container } = render(
      <RealtimeStatus
        connectionState="reconnecting"
        lastUpdateTime={null}
      />
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('text-yellow-600');
  });

  test('should display correct colors for error state', () => {
    const { container } = render(
      <RealtimeStatus
        connectionState="error"
        lastUpdateTime={null}
      />
    );

    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('text-red-600');
  });

  test('should not display time info when disconnected', () => {
    render(
      <RealtimeStatus
        connectionState="disconnected"
        lastUpdateTime={null}
      />
    );

    expect(screen.queryByText(/Updated/)).not.toBeInTheDocument();
  });

  test('should render all status states correctly', () => {
    const states = ['connected', 'connecting', 'reconnecting', 'error', 'disconnected'] as const;

    states.forEach((state) => {
      const { unmount } = render(
        <RealtimeStatus
          connectionState={state}
          lastUpdateTime={state === 'connected' ? new Date() : null}
        />
      );

      expect(screen.getByText(/●|◌|✕|○|Live|Connecting|Reconnecting|Disconnected|Offline/)).toBeInTheDocument();
      unmount();
    });
  });
});
