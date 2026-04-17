/**
 * Component displaying real-time connection status.
 */

import React from 'react';
import { ConnectionState } from '../services/websocket';

interface RealtimeStatusProps {
  connectionState: ConnectionState;
  lastUpdateTime: Date | null;
}

export function RealtimeStatus({ connectionState, lastUpdateTime }: RealtimeStatusProps) {
  const getStatusColor = (): string => {
    switch (connectionState) {
      case 'connected':
        return 'text-green-600';
      case 'reconnecting':
        return 'text-yellow-600';
      case 'connecting':
        return 'text-blue-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (): string => {
    switch (connectionState) {
      case 'connected':
        return '●';
      case 'reconnecting':
        return '◌';
      case 'connecting':
        return '◌';
      case 'error':
        return '✕';
      default:
        return '○';
    }
  };

  const getStatusLabel = (): string => {
    switch (connectionState) {
      case 'connected':
        return 'Live';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Disconnected';
      default:
        return 'Offline';
    }
  };

  const lastUpdateText = lastUpdateTime
    ? `Updated ${Math.round((Date.now() - lastUpdateTime.getTime()) / 1000)}s ago`
    : 'No updates';

  return (
    <div className={`flex items-center gap-2 text-sm ${getStatusColor()}`}>
      <span className="text-lg">{getStatusIcon()}</span>
      <span className="font-medium">{getStatusLabel()}</span>
      {connectionState === 'connected' && (
        <span className="text-gray-500 text-xs ml-1">({lastUpdateText})</span>
      )}
    </div>
  );
}
