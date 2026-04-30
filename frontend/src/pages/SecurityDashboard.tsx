import React from "react";
import { Link } from "react-router-dom";
import OWASPComplianceScorecard from "../components/OWASPComplianceScorecard";

const DEMO_KEY = "pk-demo:sk-demo-secret-123";

const SecurityDashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Security Status</h1>
            <p className="text-slate-600">OWASP LLM vulnerability compliance assessment</p>
          </div>
          <Link
            to="/configuration"
            className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition"
          >
            ⚙️ Configure Policies
          </Link>
        </div>

        {/* OWASP Scorecard */}
        <div className="mb-8">
          <OWASPComplianceScorecard demoKey={DEMO_KEY} />
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-3">How to Improve</h3>
            <ul className="space-y-2 text-sm text-slate-700">
              <li>• Review failed controls for remediation guidance</li>
              <li>• Enable additional injection patterns for LLM01</li>
              <li>• Implement supply chain dependency scanning</li>
              <li>• Add model fingerprinting for theft detection</li>
            </ul>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-3">Score Breakdown</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-700">Policy Enforcement (LLM10):</span>
                <span className="font-semibold text-green-600">✅ PASS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-700">Authentication (LLM05):</span>
                <span className="font-semibold text-green-600">✅ PASS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-700">Access Control (LLM04):</span>
                <span className="font-semibold text-green-600">✅ PASS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-700">Model Theft (LLM08):</span>
                <span className="font-semibold text-red-600">❌ FAIL</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500">
          <p>Last updated: {new Date().toLocaleTimeString()}</p>
        </div>
      </div>
    </div>
  );
};

export default SecurityDashboard;
