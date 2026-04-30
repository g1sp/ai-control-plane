import React, { useEffect, useState } from "react";

interface OWASPItem {
  id: string;
  title: string;
  status: "PASS" | "FAIL";
  description: string;
  implementation: string;
  risks: string[];
  evidence: string[];
}

interface ComplianceData {
  overallScore: number;
  totalItems: number;
  compliancePercentage: number;
  items: OWASPItem[];
}

interface Props {
  demoKey: string;
}

const OWASPComplianceScorecard: React.FC<Props> = ({ demoKey }) => {
  const [data, setData] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const baseUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  useEffect(() => {
    fetchCompliance();
    const interval = setInterval(fetchCompliance, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchCompliance = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/v1/security/owasp-compliance`, {
        headers: {
          "Authorization": `Bearer ${demoKey}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setData(data);
      }
    } catch (err) {
      console.error("Failed to fetch compliance:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-bold text-slate-900 mb-2">OWASP LLM Compliance</h2>
        <p className="text-slate-600">Loading...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-bold text-slate-900 mb-2">OWASP LLM Compliance</h2>
        <p className="text-red-600">Failed to load compliance data</p>
      </div>
    );
  }

  const complianceColor = data.compliancePercentage >= 0.7 ? "text-green-700" : data.compliancePercentage >= 0.5 ? "text-yellow-700" : "text-red-700";
  const complianceBarColor = data.compliancePercentage >= 0.7 ? "bg-green-500" : data.compliancePercentage >= 0.5 ? "bg-yellow-500" : "bg-red-500";
  const statusLabel = data.compliancePercentage >= 0.7 ? "MOSTLY COMPLIANT" : data.compliancePercentage >= 0.5 ? "PARTIALLY COMPLIANT" : "NEEDS IMPROVEMENT";

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900">OWASP LLM Top 10 Compliance</h2>
          <button
            onClick={fetchCompliance}
            className="px-3 py-1 text-sm text-slate-600 hover:text-slate-900 border border-slate-300 rounded hover:bg-slate-50"
          >
            ⟳ Refresh
          </button>
        </div>

        {/* Score Card */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <div className={`text-3xl font-bold ${complianceColor}`}>{data.overallScore}</div>
            <div className="text-sm text-slate-600">of {data.totalItems} Controls</div>
          </div>

          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <div className={`text-3xl font-bold ${complianceColor}`}>{Math.round(data.compliancePercentage * 100)}%</div>
            <div className="text-sm text-slate-600">Compliance Rate</div>
          </div>

          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <div className={`text-3xl font-bold ${complianceColor}`}>{statusLabel}</div>
            <div className="text-sm text-slate-600">Status</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-200 rounded-full h-2">
          <div
            className={`${complianceBarColor} h-2 rounded-full transition-all`}
            style={{ width: `${data.compliancePercentage * 100}%` }}
          />
        </div>
      </div>

      {/* Items Grid */}
      <div className="space-y-3">
        {data.items.map((item) => (
          <div
            key={item.id}
            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
              item.status === "PASS"
                ? "bg-green-50 border-green-200 hover:border-green-300"
                : "bg-red-50 border-red-200 hover:border-red-300"
            }`}
            onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-sm font-semibold ${item.status === "PASS" ? "text-green-900" : "text-red-900"}`}>
                    {item.id}
                  </span>
                  <span className={`text-xs font-bold px-2 py-1 rounded ${
                    item.status === "PASS"
                      ? "bg-green-200 text-green-800"
                      : "bg-red-200 text-red-800"
                  }`}>
                    {item.status === "PASS" ? "✅ PASS" : "❌ FAIL"}
                  </span>
                </div>
                <div className={`font-semibold ${item.status === "PASS" ? "text-green-900" : "text-red-900"}`}>
                  {item.title}
                </div>
                <div className={`text-sm mt-1 ${item.status === "PASS" ? "text-green-800" : "text-red-800"}`}>
                  {item.description}
                </div>
              </div>

              <div className="ml-4">
                <span className={`text-xl ${expandedId === item.id ? "rotate-180" : ""} transition-transform`}>
                  ▼
                </span>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedId === item.id && (
              <div className={`mt-4 pt-4 border-t-2 ${
                item.status === "PASS" ? "border-green-200" : "border-red-200"
              } space-y-3`}>
                <div>
                  <div className={`text-sm font-semibold ${item.status === "PASS" ? "text-green-900" : "text-red-900"}`}>
                    Implementation:
                  </div>
                  <div className={`text-sm ${item.status === "PASS" ? "text-green-800" : "text-red-800"}`}>
                    {item.implementation}
                  </div>
                </div>

                <div>
                  <div className={`text-sm font-semibold ${item.status === "PASS" ? "text-green-900" : "text-red-900"}`}>
                    Risks Mitigated:
                  </div>
                  <div className={`text-sm ${item.status === "PASS" ? "text-green-800" : "text-red-800"}`}>
                    {item.risks.join(", ")}
                  </div>
                </div>

                <div>
                  <div className={`text-sm font-semibold ${item.status === "PASS" ? "text-green-900" : "text-red-900"}`}>
                    Evidence:
                  </div>
                  <ul className={`text-sm space-y-1 ml-4 ${item.status === "PASS" ? "text-green-800" : "text-red-800"}`}>
                    {item.evidence.map((evidence, idx) => (
                      <li key={idx}>• {evidence}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OWASPComplianceScorecard;
