/**
 * Hook for managing alert channel settings.
 */

import { useEffect, useState, useCallback } from 'react';

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

export interface DeliveryRule {
  id: string;
  triggerType: string;
  channelType: string;
  enabled: boolean;
  alertLevels: string[];
}

export interface DeliveryRecord {
  id: string;
  alertId: string;
  channelType: string;
  destination: string;
  status: 'pending' | 'sent' | 'failed' | 'retrying';
  timestamp: Date;
  errorMessage?: string;
  retryCount: number;
}

export interface ChannelStats {
  totalChannels: number;
  enabledChannels: number;
  totalRules: number;
  totalDeliveries: number;
  failedDeliveries: number;
}

interface UseChannelSettingsReturn {
  channels: ChannelConfig[];
  rules: DeliveryRule[];
  history: DeliveryRecord[];
  stats: ChannelStats;
  isLoading: boolean;
  error: Error | null;
  addChannel: (channel: ChannelConfig) => Promise<void>;
  updateChannel: (channel: ChannelConfig) => Promise<void>;
  removeChannel: (channelId: string) => Promise<void>;
  addRule: (rule: DeliveryRule) => Promise<void>;
  updateRule: (rule: DeliveryRule) => Promise<void>;
  removeRule: (ruleId: string) => Promise<void>;
  testChannel: (channelId: string) => Promise<boolean>;
  getHistory: (limit?: number, status?: string) => Promise<void>;
  retryDelivery: (recordId: string) => Promise<void>;
}

export function useChannelSettings(): UseChannelSettingsReturn {
  const [channels, setChannels] = useState<ChannelConfig[]>([]);
  const [rules, setRules] = useState<DeliveryRule[]>([]);
  const [history, setHistory] = useState<DeliveryRecord[]>([]);
  const [stats, setStats] = useState<ChannelStats>({
    totalChannels: 0,
    enabledChannels: 0,
    totalRules: 0,
    totalDeliveries: 0,
    failedDeliveries: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Load initial data
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      // Fetch channels
      const channelsResponse = await fetch('/api/v1/alert-channels/channels');
      if (channelsResponse.ok) {
        const data = await channelsResponse.json();
        setChannels(data.channels || []);
      }

      // Fetch rules
      const rulesResponse = await fetch('/api/v1/alert-channels/rules');
      if (rulesResponse.ok) {
        const data = await rulesResponse.json();
        setRules(data.rules || []);
      }

      // Fetch history
      const historyResponse = await fetch('/api/v1/alert-channels/history?limit=50');
      if (historyResponse.ok) {
        const data = await historyResponse.json();
        setHistory(
          (data.records || []).map((r: any) => ({
            ...r,
            timestamp: new Date(r.timestamp),
          }))
        );
      }

      // Fetch stats
      const statsResponse = await fetch('/api/v1/alert-channels/status');
      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats(data);
      }

      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addChannel = useCallback(
    async (channel: ChannelConfig) => {
      try {
        const response = await fetch('/api/v1/alert-channels/channels', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            channel_type: channel.type,
            destination: channel.destination,
            enabled: channel.enabled,
            include_critical: channel.includeCritical,
            include_warning: channel.includeWarning,
            include_info: channel.includeInfo,
          }),
        });

        if (response.ok) {
          const newChannel = await response.json();
          setChannels((prev) => [...prev, newChannel]);
          setError(null);
        } else {
          throw new Error('Failed to add channel');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    []
  );

  const updateChannel = useCallback(
    async (channel: ChannelConfig) => {
      try {
        const response = await fetch(`/api/v1/alert-channels/channels/${channel.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            enabled: channel.enabled,
            include_critical: channel.includeCritical,
            include_warning: channel.includeWarning,
            include_info: channel.includeInfo,
          }),
        });

        if (response.ok) {
          setChannels((prev) =>
            prev.map((c) => (c.id === channel.id ? channel : c))
          );
          setError(null);
        } else {
          throw new Error('Failed to update channel');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    []
  );

  const removeChannel = useCallback(
    async (channelId: string) => {
      try {
        const response = await fetch(`/api/v1/alert-channels/channels/${channelId}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          setChannels((prev) => prev.filter((c) => c.id !== channelId));
          setError(null);
        } else {
          throw new Error('Failed to remove channel');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    []
  );

  const addRule = useCallback(
    async (rule: DeliveryRule) => {
      try {
        const response = await fetch('/api/v1/alert-channels/rules', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            trigger_type: rule.triggerType,
            channel_type: rule.channelType,
            enabled: rule.enabled,
            alert_levels: rule.alertLevels,
          }),
        });

        if (response.ok) {
          const newRule = await response.json();
          setRules((prev) => [...prev, newRule]);
          setError(null);
        } else {
          throw new Error('Failed to add rule');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    []
  );

  const updateRule = useCallback(
    async (rule: DeliveryRule) => {
      try {
        const response = await fetch(`/api/v1/alert-channels/rules/${rule.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            enabled: rule.enabled,
            alert_levels: rule.alertLevels,
          }),
        });

        if (response.ok) {
          setRules((prev) =>
            prev.map((r) => (r.id === rule.id ? rule : r))
          );
          setError(null);
        } else {
          throw new Error('Failed to update rule');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    []
  );

  const removeRule = useCallback(
    async (ruleId: string) => {
      try {
        const response = await fetch(`/api/v1/alert-channels/rules/${ruleId}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          setRules((prev) => prev.filter((r) => r.id !== ruleId));
          setError(null);
        } else {
          throw new Error('Failed to remove rule');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    []
  );

  const testChannel = useCallback(
    async (channelId: string) => {
      try {
        const channel = channels.find((c) => c.id === channelId);
        if (!channel) {
          throw new Error('Channel not found');
        }

        const response = await fetch('/api/v1/alert-channels/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            channel_type: channel.type,
            destination: channel.destination,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setError(null);
          return data.success ?? true;
        } else {
          throw new Error('Test failed');
        }
      } catch (err) {
        setError(err as Error);
        return false;
      }
    },
    [channels]
  );

  const getHistory = useCallback(
    async (limit = 50, status?: string) => {
      try {
        const url = new URL('/api/v1/alert-channels/history', window.location.origin);
        url.searchParams.append('limit', limit.toString());
        if (status) {
          url.searchParams.append('status', status);
        }

        const response = await fetch(url.toString());
        if (response.ok) {
          const data = await response.json();
          setHistory(
            (data.records || []).map((r: any) => ({
              ...r,
              timestamp: new Date(r.timestamp),
            }))
          );
          setError(null);
        } else {
          throw new Error('Failed to fetch history');
        }
      } catch (err) {
        setError(err as Error);
      }
    },
    []
  );

  const retryDelivery = useCallback(
    async (recordId: string) => {
      try {
        const response = await fetch(`/api/v1/alert-channels/history/${recordId}/retry`, {
          method: 'POST',
        });

        if (response.ok) {
          // Reload history to see updated status
          await getHistory();
          setError(null);
        } else {
          throw new Error('Failed to retry delivery');
        }
      } catch (err) {
        setError(err as Error);
        throw err;
      }
    },
    [getHistory]
  );

  return {
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
    getHistory,
    retryDelivery,
  };
}
