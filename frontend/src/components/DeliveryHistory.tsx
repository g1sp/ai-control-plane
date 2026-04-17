/**
 * Component for viewing alert delivery history.
 */

import React, { useState } from 'react';

export type DeliveryStatus = 'pending' | 'sent' | 'failed' | 'retrying';

export interface DeliveryRecord {
  id: string;
  alertId: string;
  channelType: string;
  destination: string;
  status: DeliveryStatus;
  timestamp: Date;
  errorMessage?: string;
  retryCount: number;
}

interface DeliveryHistoryProps {
  records: DeliveryRecord[];
  onRetry?: (recordId: string) => void;
}

const statusColors: Record<DeliveryStatus, string> = {
  pending: 'bg-blue-100 text-blue-800',
  sent: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  retrying: 'bg-yellow-100 text-yellow-800',
};

const statusIcons: Record<DeliveryStatus, string> = {
  pending: '⏳',
  sent: '✓',
  failed: '✗',
  retrying: '🔄',
};

export function DeliveryHistory({ records, onRetry }: DeliveryHistoryProps) {
  const [filter, setFilter] = useState<DeliveryStatus | 'all'>('all');
  const [expandedRecord, setExpandedRecord] = useState<string | null>(null);

  const filteredRecords =
    filter === 'all' ? records : records.filter((r) => r.status === filter);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Delivery History</h2>
        <p className="text-gray-600 mb-4">View recent alert deliveries and their status.</p>
      </div>

      {/* Status Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded text-sm ${
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All ({records.length})
        </button>
        {(['pending', 'sent', 'failed', 'retrying'] as DeliveryStatus[]).map((status) => {
          const count = records.filter((r) => r.status === status).length;
          return (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-1 rounded text-sm ${
                filter === status
                  ? statusColors[status]
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)} ({count})
            </button>
          );
        })}
      </div>

      {/* Delivery Records */}
      <div className="space-y-2">
        {filteredRecords.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No delivery records found
          </div>
        ) : (
          filteredRecords.map((record) => (
            <div
              key={record.id}
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              {/* Record Header */}
              <button
                onClick={() =>
                  setExpandedRecord(expandedRecord === record.id ? null : record.id)
                }
                className="w-full px-4 py-3 text-left hover:bg-gray-50 transition flex items-center justify-between"
              >
                <div className="flex items-center gap-3 flex-1">
                  <span className="text-lg">{statusIcons[record.status]}</span>
                  <div>
                    <div className="font-medium text-gray-900">{record.channelType}</div>
                    <div className="text-sm text-gray-600 truncate">{record.destination}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`inline-block px-2 py-1 rounded text-xs font-semibold ${statusColors[record.status]}`}>
                    {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                  </div>
                  <div className="text-xs text-gray-500 ml-2">
                    {new Date(record.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </button>

              {/* Record Details (Expandable) */}
              {expandedRecord === record.id && (
                <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 space-y-2">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Alert ID:</span>
                      <div className="font-mono text-gray-900">{record.alertId}</div>
                    </div>
                    <div>
                      <span className="text-gray-600">Channel:</span>
                      <div className="text-gray-900">{record.channelType}</div>
                    </div>
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <div className="text-gray-900">
                        {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Retries:</span>
                      <div className="text-gray-900">{record.retryCount}/3</div>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-600">Timestamp:</span>
                      <div className="text-gray-900">
                        {new Date(record.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  {/* Error Message */}
                  {record.errorMessage && (
                    <div className="bg-red-50 border border-red-200 rounded p-2">
                      <p className="text-xs font-medium text-red-800">Error:</p>
                      <p className="text-xs text-red-700 mt-1">{record.errorMessage}</p>
                    </div>
                  )}

                  {/* Retry Button */}
                  {record.status === 'failed' && record.retryCount < 3 && (
                    <button
                      onClick={() => onRetry?.(record.id)}
                      className="mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      Retry Delivery
                    </button>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mt-4">
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">
            {records.filter((r) => r.status === 'sent').length}
          </div>
          <div className="text-xs text-green-700 font-medium">Successful</div>
        </div>
        <div className="bg-red-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-red-600">
            {records.filter((r) => r.status === 'failed').length}
          </div>
          <div className="text-xs text-red-700 font-medium">Failed</div>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {records.filter((r) => r.status === 'pending').length}
          </div>
          <div className="text-xs text-blue-700 font-medium">Pending</div>
        </div>
        <div className="bg-yellow-50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {records.filter((r) => r.status === 'retrying').length}
          </div>
          <div className="text-xs text-yellow-700 font-medium">Retrying</div>
        </div>
      </div>
    </div>
  );
}
