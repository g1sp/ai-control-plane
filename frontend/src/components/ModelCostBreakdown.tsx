import React, { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";

interface ModelCostBreakdownProps {
  demoKey: string;
}

interface ToolCost {
  name: string;
  value: number;
}

const ModelCostBreakdown: React.FC<ModelCostBreakdownProps> = ({ demoKey }) => {
  const [data, setData] = useState<ToolCost[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCost, setTotalCost] = useState(0);

  const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

  const fetchModelCosts = async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const response = await fetch(`${baseUrl}/api/v1/analytics/tools?hours=24`, {
        headers: {
          "Authorization": `Bearer ${demoKey}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        const costs: ToolCost[] = [];
        let total = 0;

        if (result.tools) {
          Object.entries(result.tools).forEach(([toolName, toolData]: [string, any]) => {
            if (toolData && toolData.stats && toolData.stats.uses > 0) {
              const cost = toolData.stats.uses * 0.001; // Estimate cost (would come from actual pricing)
              costs.push({
                name: toolName === "claude" ? "Claude API" : toolName.charAt(0).toUpperCase() + toolName.slice(1),
                value: cost,
              });
              total += cost;
            }
          });
        }

        // If no tools data, estimate from query costs
        if (costs.length === 0) {
          const costResponse = await fetch(
            `${baseUrl}/api/v1/analytics/costs/daily?days=1`,
            {
              headers: {
                "Authorization": `Bearer ${demoKey}`,
              },
            }
          );

          if (costResponse.ok) {
            const costData = await costResponse.json();
            if (costData.total_cost) {
              costs.push(
                { name: "Claude API", value: costData.total_cost * 0.6 },
                { name: "Ollama", value: costData.total_cost * 0.4 }
              );
              total = costData.total_cost;
            }
          }
        }

        setData(costs);
        setTotalCost(total);
      }
    } catch (err) {
      console.error("Failed to fetch model costs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelCosts();
    const interval = setInterval(fetchModelCosts, 60000);
    return () => clearInterval(interval);
  }, [demoKey]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 h-80 flex items-center justify-center">
        <div className="text-slate-500">Loading model breakdown...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-bold text-slate-900 mb-4">Cost by Model (24h)</h2>

      {data.length > 0 ? (
        <div className="space-y-4">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: $${value.toFixed(3)}`}
                outerRadius={60}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => `$${value?.toFixed(4)}`}
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "none",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          <div className="space-y-2">
            <div className="text-sm font-semibold text-slate-700">Breakdown</div>
            {data.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                  />
                  <span className="text-slate-700">{item.name}</span>
                </div>
                <div className="font-semibold text-slate-900">
                  ${item.value.toFixed(4)} ({((item.value / totalCost) * 100).toFixed(0)}%)
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-slate-200">
            <div className="flex justify-between items-center">
              <span className="text-sm font-semibold text-slate-700">Total</span>
              <span className="text-lg font-bold text-slate-900">${totalCost.toFixed(3)}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="h-48 flex items-center justify-center text-slate-500">
          No model cost data available
        </div>
      )}
    </div>
  );
};

export default ModelCostBreakdown;
