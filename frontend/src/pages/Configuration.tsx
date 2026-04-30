import React, { useEffect, useState } from "react";

const DEMO_KEY = "pk-demo:sk-demo-secret-123";

interface ConfigState {
  models_whitelist: string[];
  users_whitelist: string[];
  budget_per_request: number;
  budget_per_user_per_day: number;
  rate_limit_req_per_minute: number;
  injection_patterns: string[];
}

interface HistoryItem {
  key: string;
  value: string | string[] | number;
  last_modified: string;
  modified_by: string;
}

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<ConfigState | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [editingKey, setEditingKey] = useState<string | null>(null);

  const baseUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  useEffect(() => {
    fetchConfig();
    fetchHistory();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/config`, {
        headers: {
          "Authorization": `Bearer ${DEMO_KEY}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (err) {
      setMessage({ type: "error", text: "Failed to load configuration" });
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/config/history?limit=10`, {
        headers: {
          "Authorization": `Bearer ${DEMO_KEY}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setHistory(data.history || []);
      }
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  const updateConfig = async (key: keyof ConfigState, value: string[] | number) => {
    setSaving(true);
    try {
      const response = await fetch(`${baseUrl}/api/v1/config/${key}`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${DEMO_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ value }),
      });

      if (response.ok) {
        setMessage({ type: "success", text: `Updated ${key}` });
        setEditingKey(null);
        await fetchConfig();
        await fetchHistory();
      } else {
        const error = await response.text();
        setMessage({ type: "error", text: `Error: ${error}` });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Failed to update configuration" });
    } finally {
      setSaving(false);
    }
  };

  const addToList = (key: keyof ConfigState, item: string) => {
    if (!config) return;
    const list = config[key] as string[];
    if (item && !list.includes(item)) {
      updateConfig(key, [...list, item]);
    }
  };

  const removeFromList = (key: keyof ConfigState, item: string) => {
    if (!config) return;
    const list = config[key] as string[];
    updateConfig(key, list.filter((i) => i !== item));
  };

  const getConfigLabel = (key: string): string => {
    const labels: Record<string, string> = {
      models_whitelist: "Models Whitelist",
      users_whitelist: "Users Whitelist",
      budget_per_request: "Budget per Request",
      budget_per_user_per_day: "Budget per User per Day",
      rate_limit_req_per_minute: "Rate Limit",
      injection_patterns: "Injection Patterns",
    };
    return labels[key] || key;
  };

  const getChangeColor = (previous: any, current: any): string => {
    if (typeof current === "number" && typeof previous === "number") {
      return current > previous ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200";
    }
    return "bg-blue-50 border-blue-200";
  };

  const formatValue = (value: any): string => {
    if (Array.isArray(value)) return `[${value.length} items]`;
    if (typeof value === "number") return value.toString();
    return String(value);
  };

  const rollbackConfig = async (key: string, timestamp: string) => {
    if (!window.confirm(`Restore ${getConfigLabel(key)} to previous value?`)) return;

    setSaving(true);
    try {
      const response = await fetch(`${baseUrl}/api/v1/config/rollback/${key}/${encodeURIComponent(timestamp)}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${DEMO_KEY}`,
        },
      });

      if (response.ok) {
        setMessage({ type: "success", text: `Restored ${getConfigLabel(key)}` });
        await fetchConfig();
        await fetchHistory();
      } else {
        const error = await response.text();
        setMessage({ type: "error", text: `Error: ${error}` });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Failed to rollback configuration" });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-slate-900">Configuration</h1>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-slate-900">Configuration</h1>
          <p className="text-slate-600">Failed to load configuration</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Policy Configuration</h1>
          <p className="text-slate-600">Manage gateway policies and settings</p>
        </div>

        {/* Message Toast */}
        {message && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              message.type === "success"
                ? "bg-green-50 border border-green-200 text-green-800"
                : "bg-red-50 border border-red-200 text-red-800"
            }`}
          >
            {message.type === "success" ? "✅" : "❌"} {message.text}
          </div>
        )}

        {/* Configuration Sections */}
        <div className="space-y-6">
          {/* Users Whitelist */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Allowed Users</h2>
            <div className="space-y-3">
              {config.users_whitelist.map((user) => (
                <div key={user} className="flex items-center justify-between bg-slate-50 p-3 rounded">
                  <span className="text-slate-700">{user}</span>
                  <button
                    onClick={() => removeFromList("users_whitelist", user)}
                    disabled={saving}
                    className="px-3 py-1 text-sm bg-red-50 text-red-600 hover:bg-red-100 rounded disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <div className="flex gap-2 pt-2">
                <input
                  id="new-user"
                  type="text"
                  placeholder="user@example.com"
                  className="flex-1 px-3 py-2 border border-slate-200 rounded text-sm"
                />
                <button
                  onClick={() => {
                    const input = document.getElementById("new-user") as HTMLInputElement;
                    if (input.value) {
                      addToList("users_whitelist", input.value);
                      input.value = "";
                    }
                  }}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Models Whitelist */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Allowed Models</h2>
            <div className="space-y-3">
              {config.models_whitelist.map((model) => (
                <div key={model} className="flex items-center justify-between bg-slate-50 p-3 rounded">
                  <span className="text-slate-700">{model}</span>
                  <button
                    onClick={() => removeFromList("models_whitelist", model)}
                    disabled={saving}
                    className="px-3 py-1 text-sm bg-red-50 text-red-600 hover:bg-red-100 rounded disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Budget per Request */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Budget per Request</h2>
            <div className="flex items-center gap-4">
              <span className="text-2xl font-bold text-blue-600">${config.budget_per_request.toFixed(4)}</span>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                defaultValue={config.budget_per_request}
                onBlur={(e) => {
                  const val = parseFloat(e.currentTarget.value);
                  if (val !== config.budget_per_request) {
                    updateConfig("budget_per_request", val);
                  }
                }}
                className="px-3 py-2 border border-slate-200 rounded w-24"
                placeholder="0.10"
              />
            </div>
          </div>

          {/* Budget per User per Day */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Daily Budget per User</h2>
            <div className="flex items-center gap-4">
              <span className="text-2xl font-bold text-green-600">${config.budget_per_user_per_day.toFixed(2)}</span>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1000"
                defaultValue={config.budget_per_user_per_day}
                onBlur={(e) => {
                  const val = parseFloat(e.currentTarget.value);
                  if (val !== config.budget_per_user_per_day) {
                    updateConfig("budget_per_user_per_day", val);
                  }
                }}
                className="px-3 py-2 border border-slate-200 rounded w-24"
                placeholder="10.0"
              />
            </div>
          </div>

          {/* Rate Limit */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Rate Limit</h2>
            <div className="flex items-center gap-4">
              <span className="text-2xl font-bold text-purple-600">{config.rate_limit_req_per_minute}</span>
              <span className="text-slate-600">requests per minute</span>
              <input
                type="number"
                step="1"
                min="1"
                max="10000"
                defaultValue={config.rate_limit_req_per_minute}
                onBlur={(e) => {
                  const val = parseInt(e.currentTarget.value);
                  if (val !== config.rate_limit_req_per_minute) {
                    updateConfig("rate_limit_req_per_minute", val);
                  }
                }}
                className="px-3 py-2 border border-slate-200 rounded w-24"
                placeholder="60"
              />
            </div>
          </div>

          {/* Injection Patterns (Read-only) */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Injection Detection Patterns</h2>
            <div className="text-sm text-slate-600 mb-3">Read-only (Edit in database for advanced use)</div>
            <div className="space-y-2 bg-slate-50 p-4 rounded max-h-40 overflow-y-auto">
              {config.injection_patterns.map((pattern, idx) => (
                <div key={idx} className="font-mono text-xs text-slate-600 break-words">
                  {pattern}
                </div>
              ))}
            </div>
          </div>

          {/* Configuration Timeline */}
          {history.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-4">Change Timeline</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {history.map((item: any, idx) => (
                  <div key={idx} className={`p-4 rounded-lg border-2 transition-all ${getChangeColor(item.previousValue, item.currentValue)}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-semibold text-slate-900">{getConfigLabel(item.key)}</div>
                        <div className="text-sm text-slate-700 mt-1">
                          {item.previousValue !== null ? (
                            <span>
                              <span className="font-mono text-xs">{formatValue(item.previousValue)}</span>
                              <span className="mx-2">→</span>
                              <span className="font-mono text-xs">{formatValue(item.currentValue)}</span>
                            </span>
                          ) : (
                            <span className="text-xs">Initial value: <span className="font-mono">{formatValue(item.currentValue)}</span></span>
                          )}
                        </div>
                        <div className="text-xs text-slate-600 mt-2">
                          {item.modified_by} • {new Date(item.timestamp).toLocaleString()}
                        </div>
                      </div>
                      {item.previousValue !== null && (
                        <button
                          onClick={() => rollbackConfig(item.key, item.timestamp)}
                          disabled={saving}
                          className="ml-3 px-3 py-2 text-xs bg-slate-700 text-white rounded hover:bg-slate-800 disabled:opacity-50 whitespace-nowrap"
                        >
                          ↶ Restore
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Changes take effect immediately</p>
        </div>
      </div>
    </div>
  );
};

export default Configuration;
