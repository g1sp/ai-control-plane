import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface CostTrendProps {
  demoKey: string;
}

interface CostData {
  time: string;
  cost: number;
}

const CostTrend: React.FC<CostTrendProps> = ({ demoKey }) => {
  const [data, setData] = useState<CostData[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCost, setTotalCost] = useState(0);

  const fetchCostData = async () => {
    try {
      const baseUrl = process.env.REACT_APP_API_BASE || "http://localhost:8000";
      const response = await fetch(`${baseUrl}/api/v1/analytics/costs/daily?days=1`, {
        headers: {
          "Authorization": `Bearer ${demoKey}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        const hourlyData: CostData[] = [];
        let total = 0;

        if (result.daily_costs) {
          Object.entries(result.daily_costs).forEach(([hour, cost]) => {
            hourlyData.push({
              time: hour.substring(11, 16) || hour,
              cost: cost as number,
            });
            total += cost as number;
          });
        }

        setData(hourlyData.slice(-24));
        setTotalCost(total);
      }
    } catch (err) {
      console.error("Failed to fetch cost data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostData();
    const interval = setInterval(fetchCostData, 60000);
    return () => clearInterval(interval);
  }, [demoKey]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 h-80 flex items-center justify-center">
        <div className="text-slate-500">Loading cost trend...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-bold text-slate-900 mb-4">Cost Trend (24h)</h2>

      <div className="mb-4 flex justify-between items-center">
        <div>
          <div className="text-3xl font-bold text-slate-900">${totalCost.toFixed(3)}</div>
          <div className="text-sm text-slate-600">Total today</div>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-600">Average</div>
          <div className="text-lg font-semibold text-slate-900">
            ${(totalCost / (data.length || 1)).toFixed(4)}
          </div>
        </div>
      </div>

      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="time" stroke="#94a3b8" style={{ fontSize: "12px" }} />
            <YAxis stroke="#94a3b8" style={{ fontSize: "12px" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                border: "none",
                borderRadius: "8px",
                color: "#fff",
              }}
              formatter={(value) => `$${value?.toFixed(4)}`}
            />
            <Line
              type="monotone"
              dataKey="cost"
              stroke="#3b82f6"
              dot={false}
              strokeWidth={2}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-48 flex items-center justify-center text-slate-500">
          No cost data available
        </div>
      )}
    </div>
  );
};

export default CostTrend;
