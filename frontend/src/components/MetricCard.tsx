/**
 * Reusable metric card component
 */

import React from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: "blue" | "green" | "red" | "yellow" | "purple";
  icon?: React.ReactNode;
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
  subtitle,
  color = "blue",
  icon,
}) => {
  return (
    <div className={`border-l-4 rounded p-4 ${colorClasses[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-600">{title}</p>
          <p className={`text-2xl font-bold mt-2 ${valueColorClasses[color]}`}>
            {value}
          </p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="text-2xl">{icon}</div>}
      </div>
    </div>
  );
};

export default MetricCard;
