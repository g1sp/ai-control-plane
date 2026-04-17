/**
 * Settings page for dashboard configuration.
 */

import React, { useState } from 'react';
import ChannelSettings, { ChannelConfig } from '../components/ChannelSettings';
import DeliveryRules, { DeliveryRule } from '../components/DeliveryRules';
import DeliveryHistory, { DeliveryRecord } from '../components/DeliveryHistory';
import { useChannelSettings } from '../hooks/useChannelSettings';

type SettingsTab = 'channels' | 'rules' | 'history';

const TRIGGER_TYPES = [
  'high_cost_query',
  'slow_query',
  'error_spike',
  'cost_budget_exceeded',
  'system_degradation',
];

const CHANNEL_TYPE_LABELS: Record<string, string> = {
  email: 'Email',
  slack: 'Slack',
  pagerduty: 'PagerDuty',
};

export function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('channels');
  const {
    channels,
    rules,
    history,
    stats,
    isLoading,
    error,
    addChannel,
    updateChannel,
    removeChannel,
    addRule,
    updateRule,
    removeRule,
    testChannel,
    retryDelivery,
  } = useChannelSettings();

  const handleAddChannel = async (channel: ChannelConfig) => {
    try {
      await addChannel(channel);
    } catch (err) {
      console.error('Failed to add channel:', err);
    }
  };

  const handleUpdateChannel = async (channel: ChannelConfig) => {
    try {
      await updateChannel(channel);
    } catch (err) {
      console.error('Failed to update channel:', err);
    }
  };

  const handleRemoveChannel = async (channelId: string) => {
    if (confirm('Are you sure you want to remove this channel?')) {
      try {
        await removeChannel(channelId);
      } catch (err) {
        console.error('Failed to remove channel:', err);
      }
    }
  };

  const handleAddRule = async (rule: DeliveryRule) => {
    try {
      await addRule(rule);
    } catch (err) {
      console.error('Failed to add rule:', err);
    }
  };

  const handleUpdateRule = async (rule: DeliveryRule) => {
    try {
      await updateRule(rule);
    } catch (err) {
      console.error('Failed to update rule:', err);
    }
  };

  const handleRemoveRule = async (ruleId: string) => {
    if (confirm('Are you sure you want to remove this rule?')) {
      try {
        await removeRule(ruleId);
      } catch (err) {
        console.error('Failed to remove rule:', err);
      }
    }
  };

  const handleTestChannel = async (channelId: string) => {
    try {
      return await testChannel(channelId);
    } catch (err) {
      console.error('Failed to test channel:', err);
      return false;
    }
  };

  const handleRetryDelivery = async (recordId: string) => {
    try {
      await retryDelivery(recordId);
    } catch (err) {
      console.error('Failed to retry delivery:', err);
    }
  };

  const getEnabledChannelTypes = (): string[] => {
    const types = new Set<string>();
    channels.forEach((c) => {
      if (c.enabled) {
        types.add(CHANNEL_TYPE_LABELS[c.type]);
      }
    });
    return Array.from(types);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Manage alert channels and delivery rules</p>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm font-medium">
              Error: {error.message}
            </p>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex gap-8" aria-label="Settings tabs">
            {(['channels', 'rules', 'history'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-4 font-medium text-sm border-b-2 transition ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab === 'channels' && 'Alert Channels'}
                {tab === 'rules' && 'Delivery Rules'}
                {tab === 'history' && 'Delivery History'}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Stats Bar */}
      {!isLoading && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-gray-600 text-sm">Enabled Channels</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.enabledChannels}/{stats.totalChannels}
                </p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Delivery Rules</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalRules}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Deliveries Sent</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.totalDeliveries - stats.failedDeliveries}
                </p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Failed Deliveries</p>
                <p className="text-2xl font-bold text-red-600">{stats.failedDeliveries}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Channels Tab */}
            {activeTab === 'channels' && (
              <ChannelSettings
                channels={channels}
                onAddChannel={handleAddChannel}
                onUpdateChannel={handleUpdateChannel}
                onRemoveChannel={handleRemoveChannel}
                onTestChannel={handleTestChannel}
              />
            )}

            {/* Rules Tab */}
            {activeTab === 'rules' && (
              <DeliveryRules
                rules={rules}
                channels={getEnabledChannelTypes()}
                triggerTypes={TRIGGER_TYPES}
                onAddRule={handleAddRule}
                onUpdateRule={handleUpdateRule}
                onRemoveRule={handleRemoveRule}
              />
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <DeliveryHistory
                records={history}
                onRetry={handleRetryDelivery}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Settings;
