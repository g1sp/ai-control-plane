/**
 * Component for managing alert delivery channels.
 */

import React, { useState } from 'react';

export type ChannelType = 'email' | 'slack' | 'pagerduty';

export interface ChannelConfig {
  id: string;
  type: ChannelType;
  destination: string;
  enabled: boolean;
  includeCritical: boolean;
  includeWarning: boolean;
  includeInfo: boolean;
}

interface ChannelSettingsProps {
  channels: ChannelConfig[];
  onAddChannel?: (channel: ChannelConfig) => void;
  onUpdateChannel?: (channel: ChannelConfig) => void;
  onRemoveChannel?: (channelId: string) => void;
  onTestChannel?: (channelId: string) => Promise<boolean>;
}

const channelLabels: Record<ChannelType, string> = {
  email: 'Email',
  slack: 'Slack',
  pagerduty: 'PagerDuty',
};

const channelPlaceholders: Record<ChannelType, string> = {
  email: 'alerts@example.com',
  slack: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
  pagerduty: 'Your PagerDuty Integration Key',
};

export function ChannelSettings({
  channels,
  onAddChannel,
  onUpdateChannel,
  onRemoveChannel,
  onTestChannel,
}: ChannelSettingsProps) {
  const [isAddingChannel, setIsAddingChannel] = useState(false);
  const [newChannelType, setNewChannelType] = useState<ChannelType>('email');
  const [newChannelDestination, setNewChannelDestination] = useState('');
  const [testingChannelId, setTestingChannelId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  const handleAddChannel = () => {
    if (!newChannelDestination.trim()) {
      return;
    }

    const newChannel: ChannelConfig = {
      id: `${newChannelType}-${Date.now()}`,
      type: newChannelType,
      destination: newChannelDestination,
      enabled: true,
      includeCritical: true,
      includeWarning: true,
      includeInfo: false,
    };

    onAddChannel?.(newChannel);
    setNewChannelDestination('');
    setIsAddingChannel(false);
  };

  const handleTestChannel = async (channelId: string) => {
    setTestingChannelId(channelId);
    try {
      const result = await onTestChannel?.(channelId);
      setTestResults((prev) => ({ ...prev, [channelId]: result ?? false }));
    } finally {
      setTestingChannelId(null);
    }
  };

  const handleToggleChannel = (channel: ChannelConfig) => {
    onUpdateChannel?.({ ...channel, enabled: !channel.enabled });
  };

  const handleToggleSeverity = (
    channel: ChannelConfig,
    severity: 'critical' | 'warning' | 'info'
  ) => {
    const updates: Partial<ChannelConfig> = {};
    if (severity === 'critical') {
      updates.includeCritical = !channel.includeCritical;
    } else if (severity === 'warning') {
      updates.includeWarning = !channel.includeWarning;
    } else if (severity === 'info') {
      updates.includeInfo = !channel.includeInfo;
    }
    onUpdateChannel?.({ ...channel, ...updates });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Alert Channels</h2>
        <p className="text-gray-600 mb-4">
          Configure where alerts should be delivered. Choose from email, Slack, or PagerDuty.
        </p>
      </div>

      {/* Channels List */}
      <div className="space-y-4">
        {channels.map((channel) => (
          <div key={channel.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={channel.enabled}
                  onChange={() => handleToggleChannel(channel)}
                  className="rounded"
                />
                <div>
                  <h3 className="font-semibold text-gray-900">{channelLabels[channel.type]}</h3>
                  <p className="text-sm text-gray-600 truncate">{channel.destination}</p>
                </div>
              </div>
              <button
                onClick={() => onRemoveChannel?.(channel.id)}
                className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
              >
                Remove
              </button>
            </div>

            {/* Severity Filters */}
            <div className="ml-8 flex gap-4 mb-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={channel.includeCritical}
                  onChange={() => handleToggleSeverity(channel, 'critical')}
                  disabled={!channel.enabled}
                />
                <span className="text-sm text-red-600 font-medium">Critical</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={channel.includeWarning}
                  onChange={() => handleToggleSeverity(channel, 'warning')}
                  disabled={!channel.enabled}
                />
                <span className="text-sm text-yellow-600 font-medium">Warning</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={channel.includeInfo}
                  onChange={() => handleToggleSeverity(channel, 'info')}
                  disabled={!channel.enabled}
                />
                <span className="text-sm text-blue-600 font-medium">Info</span>
              </label>
            </div>

            {/* Test Button */}
            <div className="ml-8">
              <button
                onClick={() => handleTestChannel(channel.id)}
                disabled={testingChannelId === channel.id || !channel.enabled}
                className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
              >
                {testingChannelId === channel.id ? 'Testing...' : 'Send Test'}
              </button>
              {testResults[channel.id] === true && (
                <span className="ml-2 text-sm text-green-600">✓ Test succeeded</span>
              )}
              {testResults[channel.id] === false && (
                <span className="ml-2 text-sm text-red-600">✗ Test failed</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Add Channel Form */}
      {!isAddingChannel ? (
        <button
          onClick={() => setIsAddingChannel(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Add Channel
        </button>
      ) : (
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Add Alert Channel</h3>

          <div className="space-y-3">
            {/* Channel Type Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Channel Type
              </label>
              <select
                value={newChannelType}
                onChange={(e) => setNewChannelType(e.target.value as ChannelType)}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              >
                <option value="email">Email</option>
                <option value="slack">Slack</option>
                <option value="pagerduty">PagerDuty</option>
              </select>
            </div>

            {/* Destination Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination
              </label>
              <input
                type="text"
                value={newChannelDestination}
                onChange={(e) => setNewChannelDestination(e.target.value)}
                placeholder={channelPlaceholders[newChannelType]}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              />
              <p className="text-xs text-gray-500 mt-1">
                {newChannelType === 'email' && 'Enter email address'}
                {newChannelType === 'slack' && 'Paste your Slack webhook URL'}
                {newChannelType === 'pagerduty' && 'Enter your integration key'}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleAddChannel}
                disabled={!newChannelDestination.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Add Channel
              </button>
              <button
                onClick={() => {
                  setIsAddingChannel(false);
                  setNewChannelDestination('');
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
