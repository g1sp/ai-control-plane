import React, { useEffect, useState } from "react";

interface QueryRecord {
  id: string;
  timestamp: string;
  user_id: string;
  prompt: string;
  response: string;
  model_used: string;
  cost_usd: number;
  duration_ms: number;
  policy_decision: string;
  error_message?: string;
}

interface QueryTimelineProps {
  demoKey: string;
}

interface ExpandedQuery {
  id: string | null;
}

const QueryTimeline: React.FC<QueryTimelineProps> = ({ demoKey }) => {
  const [queries, setQueries] = useState<QueryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<ExpandedQuery>({ id: null });

  const fetchQueries = async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const response = await fetch(`${baseUrl}/audit?hours=24&limit=10`, {
        headers: {
          "Authorization": `Bearer ${demoKey}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setQueries((data.records || []).slice(0, 10));
      }
    } catch (err) {
      console.error("Failed to fetch queries:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueries();
    const interval = setInterval(fetchQueries, 30000);
    return () => clearInterval(interval);
  }, [demoKey]);

  const getStatusColor = (decision: string) => {
    if (decision === "approved") return "bg-green-50 border-green-200";
    if (decision === "rejected") return "bg-red-50 border-red-200";
    return "bg-yellow-50 border-yellow-200";
  };

  const getStatusBadge = (decision: string) => {
    if (decision === "approved") return "✅ Approved";
    if (decision === "rejected") return "❌ Rejected";
    return "⚠️ Violation";
  };

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return <div className="text-slate-500">Loading recent queries...</div>;
  }

  if (queries.length === 0) {
    return <div className="text-slate-500 text-center py-8">No queries in the last 24 hours</div>;
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {queries.map((query) => (
        <div
          key={query.id}
          className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${getStatusColor(
            query.policy_decision
          )} hover:shadow-md`}
          onClick={() =>
            setExpanded({
              id: expanded.id === query.id ? null : query.id,
            })
          }
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-2">
            <div>
              <div className="font-semibold text-slate-900 truncate max-w-md">
                {query.prompt.substring(0, 60)}...
              </div>
              <div className="text-xs text-slate-600 mt-1">
                {formatTime(query.timestamp)} • User: {query.user_id}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-slate-900">${query.cost_usd.toFixed(4)}</div>
              <div className="text-xs text-slate-600">{query.duration_ms}ms</div>
            </div>
          </div>

          {/* Status and Model */}
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              <span className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-xs font-medium">
                {query.model_used}
              </span>
              <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs">
                {getStatusBadge(query.policy_decision)}
              </span>
            </div>
            {expanded.id === query.id && <span className="text-lg">▼</span>}
          </div>

          {/* Expanded Details */}
          {expanded.id === query.id && (
            <div className="mt-4 pt-4 border-t border-slate-300 space-y-3">
              <div>
                <div className="text-xs font-semibold text-slate-700 mb-1">Prompt</div>
                <div className="bg-white p-3 rounded text-sm text-slate-700 max-h-40 overflow-y-auto font-mono">
                  {query.prompt}
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-slate-700 mb-1">Response</div>
                <div className="bg-white p-3 rounded text-sm text-slate-700 max-h-40 overflow-y-auto font-mono">
                  {query.response || "No response"}
                </div>
              </div>

              {query.error_message && (
                <div>
                  <div className="text-xs font-semibold text-red-700 mb-1">Error</div>
                  <div className="bg-red-50 p-3 rounded text-sm text-red-700 font-mono">
                    {query.error_message}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-xs font-semibold text-slate-600">ID</div>
                  <div className="text-xs text-slate-500 font-mono">{query.id}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-600">Tokens In/Out</div>
                  <div className="text-xs text-slate-500">{query.id}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default QueryTimeline;
