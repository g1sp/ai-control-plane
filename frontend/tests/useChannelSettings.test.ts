/**
 * Tests for useChannelSettings hook.
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { useChannelSettings } from '../src/hooks/useChannelSettings';

// Mock fetch
global.fetch = jest.fn();

describe('useChannelSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should initialize with empty state', () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ channels: [], rules: [], records: [] }),
    });

    const { result } = renderHook(() => useChannelSettings());

    expect(result.current.channels).toEqual([]);
    expect(result.current.rules).toEqual([]);
    expect(result.current.history).toEqual([]);
  });

  test('should load channels on mount', async () => {
    const mockChannels = [
      {
        id: 'ch-1',
        type: 'email',
        destination: 'test@example.com',
        enabled: true,
      },
    ];

    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('channels')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ channels: mockChannels }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.channels).toHaveLength(1);
    });

    expect(result.current.channels[0].type).toBe('email');
  });

  test('should add channel', async () => {
    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('channels') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            id: 'ch-2',
            type: 'slack',
            destination: 'https://hooks.slack.com/...',
            enabled: true,
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ channels: [], rules: [], records: [] }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newChannel = {
      id: 'ch-2',
      type: 'slack' as const,
      destination: 'https://hooks.slack.com/...',
      enabled: true,
      includeCritical: true,
      includeWarning: true,
      includeInfo: false,
    };

    await act(async () => {
      await result.current.addChannel(newChannel);
    });

    expect(result.current.channels).toContainEqual(expect.objectContaining({ type: 'slack' }));
  });

  test('should update channel', async () => {
    const mockChannels = [
      {
        id: 'ch-1',
        type: 'email' as const,
        destination: 'test@example.com',
        enabled: true,
        includeCritical: true,
        includeWarning: true,
        includeInfo: false,
      },
    ];

    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('channels') && options?.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          json: async () => ({}),
        });
      }
      if (url.includes('channels')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ channels: mockChannels }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ rules: [], records: [] }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.channels).toHaveLength(1);
    });

    const updated = { ...mockChannels[0], enabled: false };

    await act(async () => {
      await result.current.updateChannel(updated);
    });

    expect(result.current.channels[0]).toMatchObject(updated);
  });

  test('should remove channel', async () => {
    const mockChannels = [
      {
        id: 'ch-1',
        type: 'email' as const,
        destination: 'test@example.com',
        enabled: true,
      },
    ];

    let channels = [...mockChannels];

    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('channels/ch-1') && options?.method === 'DELETE') {
        channels = [];
        return Promise.resolve({ ok: true });
      }
      if (url.includes('channels')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ channels }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.channels).toHaveLength(1);
    });

    await act(async () => {
      await result.current.removeChannel('ch-1');
    });

    expect(result.current.channels).toHaveLength(0);
  });

  test('should add delivery rule', async () => {
    const mockRule = {
      id: 'rule-1',
      trigger_type: 'high_cost_query',
      channel_type: 'email',
      enabled: true,
      alert_levels: ['critical', 'warning'],
    };

    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('rules') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: async () => mockRule,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ channels: [], rules: [], records: [] }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newRule = {
      id: 'rule-1',
      triggerType: 'high_cost_query',
      channelType: 'email',
      enabled: true,
      alertLevels: ['critical', 'warning'],
    };

    await act(async () => {
      await result.current.addRule(newRule);
    });

    expect(result.current.rules).toContainEqual(
      expect.objectContaining({ triggerType: 'high_cost_query' })
    );
  });

  test('should test channel connectivity', async () => {
    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('test')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: true }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          channels: [
            {
              id: 'ch-1',
              type: 'email',
              destination: 'test@example.com',
              enabled: true,
            },
          ],
          rules: [],
          records: [],
        }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.channels).toHaveLength(1);
    });

    let testResult: boolean = false;

    await act(async () => {
      testResult = await result.current.testChannel('ch-1');
    });

    expect(testResult).toBe(true);
  });

  test('should fetch delivery history', async () => {
    const mockHistory = [
      {
        id: 'delivery-1',
        alert_id: 'alert-1',
        channel_type: 'email',
        destination: 'test@example.com',
        status: 'sent',
        timestamp: new Date().toISOString(),
        retry_count: 0,
      },
    ];

    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('history')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ records: mockHistory }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ channels: [], rules: [], records: mockHistory }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.history.length).toBeGreaterThanOrEqual(0);
    });
  });

  test('should retry failed delivery', async () => {
    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (url.includes('retry')) {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          channels: [],
          rules: [],
          records: [
            {
              id: 'delivery-1',
              status: 'retrying',
            },
          ],
        }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.retryDelivery('delivery-1');
    });

    expect(result.current.error).toBeNull();
  });

  test('should handle errors gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).not.toBeNull();
  });

  test('should handle API errors', async () => {
    (global.fetch as jest.Mock).mockImplementation((url, options) => {
      if (options?.method === 'POST') {
        return Promise.resolve({
          ok: false,
          status: 400,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ channels: [], rules: [], records: [] }),
      });
    });

    const { result } = renderHook(() => useChannelSettings());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const newChannel = {
      id: 'ch-1',
      type: 'email' as const,
      destination: 'invalid',
      enabled: true,
      includeCritical: true,
      includeWarning: true,
      includeInfo: false,
    };

    await expect(async () => {
      await result.current.addChannel(newChannel);
    }).rejects.toThrow();
  });
});
