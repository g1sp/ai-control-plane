/**
 * Tests for RealtimeContext and provider.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { RealtimeProvider, useRealtimeContext } from '../src/context/RealtimeContext';

const TestComponent = () => {
  const context = useRealtimeContext();
  return (
    <div>
      <div data-testid="connection-state">{context.connectionState}</div>
      <div data-testid="is-connected">{context.isConnected ? 'connected' : 'disconnected'}</div>
      <div data-testid="is-reconnecting">{context.isReconnecting ? 'reconnecting' : 'not-reconnecting'}</div>
      <div data-testid="error">{context.error?.message || 'no-error'}</div>
      <div data-testid="last-update">
        {context.lastUpdateTime ? context.lastUpdateTime.getTime() : 'no-update'}
      </div>
    </div>
  );
};

describe('RealtimeContext', () => {
  test('should provide context values to consumers', () => {
    const now = new Date();

    render(
      <RealtimeProvider
        connectionState="connected"
        isConnected={true}
        isReconnecting={false}
        error={null}
        lastUpdateTime={now}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('connection-state')).toHaveTextContent('connected');
    expect(screen.getByTestId('is-connected')).toHaveTextContent('connected');
    expect(screen.getByTestId('is-reconnecting')).toHaveTextContent('not-reconnecting');
    expect(screen.getByTestId('error')).toHaveTextContent('no-error');
    expect(screen.getByTestId('last-update')).toHaveTextContent(now.getTime().toString());
  });

  test('should handle disconnected state', () => {
    render(
      <RealtimeProvider
        connectionState="disconnected"
        isConnected={false}
        isReconnecting={false}
        error={null}
        lastUpdateTime={null}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('connection-state')).toHaveTextContent('disconnected');
    expect(screen.getByTestId('is-connected')).toHaveTextContent('disconnected');
  });

  test('should handle reconnecting state', () => {
    render(
      <RealtimeProvider
        connectionState="reconnecting"
        isConnected={false}
        isReconnecting={true}
        error={null}
        lastUpdateTime={null}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('connection-state')).toHaveTextContent('reconnecting');
    expect(screen.getByTestId('is-reconnecting')).toHaveTextContent('reconnecting');
  });

  test('should handle error state', () => {
    const error = new Error('Connection failed');

    render(
      <RealtimeProvider
        connectionState="error"
        isConnected={false}
        isReconnecting={false}
        error={error}
        lastUpdateTime={null}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('connection-state')).toHaveTextContent('error');
    expect(screen.getByTestId('error')).toHaveTextContent('Connection failed');
  });

  test('should throw error when used without provider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation();

    expect(() => render(<TestComponent />)).toThrow(
      'useRealtimeContext must be used within RealtimeProvider'
    );

    consoleError.mockRestore();
  });

  test('should update context values on rerender', () => {
    const { rerender } = render(
      <RealtimeProvider
        connectionState="connecting"
        isConnected={false}
        isReconnecting={false}
        error={null}
        lastUpdateTime={null}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('connection-state')).toHaveTextContent('connecting');

    rerender(
      <RealtimeProvider
        connectionState="connected"
        isConnected={true}
        isReconnecting={false}
        error={null}
        lastUpdateTime={new Date()}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('connection-state')).toHaveTextContent('connected');
    expect(screen.getByTestId('is-connected')).toHaveTextContent('connected');
  });

  test('should handle all connection states', () => {
    const states = ['connecting', 'connected', 'reconnecting', 'error', 'disconnected'] as const;

    states.forEach((state) => {
      const { unmount } = render(
        <RealtimeProvider
          connectionState={state}
          isConnected={state === 'connected'}
          isReconnecting={state === 'reconnecting'}
          error={state === 'error' ? new Error('Test error') : null}
          lastUpdateTime={state === 'connected' ? new Date() : null}
        >
          <TestComponent />
        </RealtimeProvider>
      );

      expect(screen.getByTestId('connection-state')).toHaveTextContent(state);
      unmount();
    });
  });

  test('should provide null last update time', () => {
    render(
      <RealtimeProvider
        connectionState="connecting"
        isConnected={false}
        isReconnecting={false}
        error={null}
        lastUpdateTime={null}
      >
        <TestComponent />
      </RealtimeProvider>
    );

    expect(screen.getByTestId('last-update')).toHaveTextContent('no-update');
  });
});
