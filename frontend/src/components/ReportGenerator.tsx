/**
 * Report Generator component
 */

import React, { useState } from "react";

interface ReportGeneratorProps {
  onReportGenerated?: (reportData: { filename: string; format: string }) => void;
}

export const ReportGeneratorComponent: React.FC<ReportGeneratorProps> = ({
  onReportGenerated,
}) => {
  const [reportType, setReportType] = useState<"daily" | "weekly" | "monthly">("daily");
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("csv");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const endpoint = `/api/v1/reports/${reportType}?format=${exportFormat}`;
      const response = await fetch(endpoint);

      if (!response.ok) {
        throw new Error(`Failed to generate report: ${response.statusText}`);
      }

      const data = await response.json();

      // Create blob and download
      const content = data.report;
      const mimeType = exportFormat === "csv" ? "text/csv" : "application/json";
      const blob = new Blob([content], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      if (onReportGenerated) {
        onReportGenerated({
          filename: data.filename,
          format: exportFormat,
        });
      }

      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Generate Reports</h2>

      <div className="space-y-6">
        {/* Report Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Report Type
          </label>
          <div className="grid grid-cols-3 gap-3">
            {(["daily", "weekly", "monthly"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setReportType(type)}
                className={`py-3 px-4 rounded-lg font-medium transition ${
                  reportType === type
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Export Format Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Export Format
          </label>
          <div className="grid grid-cols-2 gap-3">
            {(["csv", "json"] as const).map((format) => (
              <button
                key={format}
                onClick={() => setExportFormat(format)}
                className={`py-3 px-4 rounded-lg font-medium transition ${
                  exportFormat === format
                    ? "bg-green-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-800">Report generated and downloaded successfully!</p>
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={generateReport}
          disabled={loading}
          className={`w-full py-3 px-4 rounded-lg font-medium transition ${
            loading
              ? "bg-gray-400 text-white cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800"
          }`}
        >
          {loading ? "Generating..." : "Generate & Download Report"}
        </button>

        {/* Report Description */}
        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600 space-y-2">
          <p>
            <strong className="text-gray-900">Daily Report:</strong> Includes today's metrics,
            queries, costs, and performance data.
          </p>
          <p>
            <strong className="text-gray-900">Weekly Report:</strong> 7-day rolling analysis with
            trends, top users, and top tools.
          </p>
          <p>
            <strong className="text-gray-900">Monthly Report:</strong> 30-day comprehensive report
            with trends, active users, and forecasts.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReportGeneratorComponent;
