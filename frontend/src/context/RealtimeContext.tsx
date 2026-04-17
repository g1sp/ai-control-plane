/**
 * Context for managing real-time connection state across dashboard.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { ConnectionState } from '../services/websocket';

interface RealtimeContextType {
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;
  error: Error | null;
  lastUpdateTime: Date | null;
}

const RealtimeContext = createContext<RealtimeContextType | undefined>(undefined);

interface RealtimeProviderProps {
  children: ReactNode;
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;
  error: Error | null;
  lastUpdateTime: Date | null;
}

export function RealtimeProvider({
  children,
  connectionState,
  isConnected,
  isReconnecting,
  error,
  lastUpdateTime,
}: RealtimeProviderProps) {
  return (
    <RealtimeContext.Provider
      value={{
        connectionState,
        isConnected,
        isReconnecting,
        error,
        lastUpdateTime,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtimeContext(): RealtimeContextType {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtimeContext must be used within RealtimeProvider');
  }
  return context;
}
