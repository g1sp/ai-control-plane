import React, { useEffect, useState } from "react";

interface HealthStatusProps {
  demoKey: string;
}

interface HealthData {
  status: string;
  gateway_version: string;
  models_available: string[];
  ollama_available: boolean;
  claude_api_key_valid: boolean;
  uptime_seconds: number;
  requests_today: number;
  cost_today_usd: number;
}

const HealthStatus: React.FC<HealthStatusProps> = ({ demoKey }) => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const response = await fetch(`${baseUrl}/health`, {
        headers: {
          "Authorization": `Bearer ${demoKey}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      }
    } catch (err) {
      console.error("Failed to fetch health:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, [demoKey]);

  if (loading || !health) {
    return <div className="text-slate-500">Loading health status...</div>;
  }

  const getStatusColor = (available: boolean) =>
    available ? "bg-green-100 border-green-300" : "bg-red-100 border-red-300";
  const getStatusText = (available: boolean) => (available ? "✅ Online" : "❌ Offline");

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-bold text-slate-900 mb-4">Service Health</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Ollama Status */}
        <div className={`p-4 rounded-lg border-2 ${getStatusColor(health.ollama_available)}`}>
          <div className="text-sm font-semibold text-slate-700 mb-2">Ollama</div>
          <div className={health.ollama_available ? "text-green-700" : "text-red-700"}>
            {getStatusText(health.ollama_available)}
          </div>
        </div>

        {/* Claude API Status */}
        <div className={`p-4 rounded-lg border-2 ${getStatusColor(health.claude_api_key_valid)}`}>
          <div className="text-sm font-semibold text-slate-700 mb-2">Claude API</div>
          <div className={health.claude_api_key_valid ? "text-green-700" : "text-red-700"}>
            {getStatusText(health.claude_api_key_valid)}
          </div>
        </div>

        {/* Gateway Status */}
        <div className="p-4 rounded-lg border-2 bg-blue-100 border-blue-300">
          <div className="text-sm font-semibold text-slate-700 mb-2">Gateway</div>
          <div className="text-blue-700">✅ Running</div>
          <div className="text-xs text-slate-600 mt-1">v{health.gateway_version || "1.1"}</div>
        </div>

        {/* Uptime */}
        <div className="p-4 rounded-lg border-2 border-slate-300 bg-slate-50">
          <div className="text-sm font-semibold text-slate-700 mb-2">Uptime</div>
          <div className="text-slate-900">{formatUptime(health.uptime_seconds)}</div>
        </div>

        {/* Quick Stats */}
        <div className="p-4 rounded-lg border-2 border-purple-300 bg-purple-50">
          <div className="text-sm font-semibold text-slate-700 mb-2">Today</div>
          <div className="text-purple-900 text-sm">
            <div>{health.requests_today} queries</div>
            <div>${health.cost_today_usd.toFixed(2)}</div>
          </div>
        </div>
      </div>

      {/* Models Available */}
      <div className="mt-4 pt-4 border-t border-slate-200">
        <div className="text-sm font-semibold text-slate-700 mb-2">Available Models</div>
        <div className="flex flex-wrap gap-2">
          {health.models_available && health.models_available.length > 0 ? (
            health.models_available.map((model) => (
              <span key={model} className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-medium">
                {model}
              </span>
            ))
          ) : (
            <span className="text-slate-500 text-sm">No models available</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthStatus;
