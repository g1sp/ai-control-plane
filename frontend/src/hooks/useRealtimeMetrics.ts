/**
 * Hook for establishing and managing real-time metrics WebSocket connection.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketClient, ConnectionState, MetricsEvent } from '../services/websocket';

interface UseRealtimeMetricsReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;
  error: Error | null;
  subscribe: (eventType: string, handler: (event: MetricsEvent) => void) => () => void;
  onStateChange: (handler: (state: ConnectionState) => void) => () => void;
}

let globalClient: WebSocketClient | null = null;
let clientRefCount = 0;

function getOrCreateClient(userId: string): WebSocketClient {
  if (!globalClient) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const baseUrl = process.env.REACT_APP_API_BASE || window.location.origin;
    const wsUrl = baseUrl.replace(/^https?/, protocol === 'wss:' ? 'wss' : 'ws');
    const url = `${wsUrl}/api/v1/analytics/stream/${userId}`;
    globalClient = new WebSocketClient(url);
  }
  return globalClient;
}

export function useRealtimeMetrics(userId: string): UseRealtimeMetricsReturn {
  const clientRef = useRef<WebSocketClient | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Get or create global client
    const client = getOrCreateClient(userId);
    clientRef.current = client;
    clientRefCount++;

    // Subscribe to state changes
    const unsubscribeStateChange = client.onStateChange((state) => {
      setConnectionState(state);
      if (state === 'error') {
        setError(new Error('WebSocket connection error'));
      } else if (state === 'connected') {
        setError(null);
      }
    });

    // Connect if not already connected
    if (!client.isConnected()) {
      client.connect().catch((err) => {
        console.error('Failed to connect:', err);
        setError(err as Error);
      });
    } else {
      setConnectionState(client.getState());
    }

    return () => {
      clientRefCount--;
      unsubscribeStateChange();

      // Disconnect global client when no more subscribers
      if (clientRefCount <= 0) {
        if (globalClient) {
          globalClient.disconnect();
          globalClient = null;
        }
        clientRef.current = null;
      }
    };
  }, [userId]);

  const subscribe = useCallback(
    (eventType: string, handler: (event: MetricsEvent) => void) => {
      if (!clientRef.current) {
        return () => {};
      }
      return clientRef.current.subscribe(eventType, handler);
    },
    []
  );

  const onStateChange = useCallback(
    (handler: (state: ConnectionState) => void) => {
      if (!clientRef.current) {
        return () => {};
      }
      return clientRef.current.onStateChange(handler);
    },
    []
  );

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    isReconnecting: connectionState === 'reconnecting',
    error,
    subscribe,
    onStateChange,
  };
}
