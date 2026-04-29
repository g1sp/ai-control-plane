import React from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  color?: "blue" | "green" | "red" | "yellow" | "purple";
  icon?: React.ReactNode;
  trend?: "up" | "down" | "stable" | "loading";
}

const colorClasses = {
  blue: "border-blue-500 bg-blue-50",
  green: "border-green-500 bg-green-50",
  red: "border-red-500 bg-red-50",
  yellow: "border-yellow-500 bg-yellow-50",
  purple: "border-purple-500 bg-purple-50",
};

const valueColorClasses = {
  blue: "text-blue-600",
  green: "text-green-600",
  red: "text-red-600",
  yellow: "text-yellow-600",
  purple: "text-purple-600",
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  color = "blue",
  icon,
  trend = "stable",
}) => {
  const getTrendIndicator = () => {
    if (trend === "loading") return "⟳";
    if (trend === "up") return "↑";
    if (trend === "down") return "↓";
    return "→";
  };

  return (
    <div className={`border-l-4 rounded-lg p-6 ${colorClasses[color]} shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-semibold text-slate-600">{title}</p>
          <div className="flex items-baseline gap-2 mt-2">
            <p className={`text-3xl font-bold ${valueColorClasses[color]}`}>
              {value}
            </p>
            {unit && <p className="text-sm text-slate-600">{unit}</p>}
          </div>
          {subtitle && <p className="text-xs text-slate-500 mt-2">{subtitle}</p>}
        </div>
        <div className="flex items-start gap-2">
          <div className="text-3xl">{icon}</div>
          <div className={`text-xl ${trend === "loading" ? "animate-spin" : ""}`}>
            {getTrendIndicator()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
