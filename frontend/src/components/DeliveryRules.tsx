/**
 * Component for managing alert delivery rules.
 */

import React, { useState } from 'react';

export type AlertLevel = 'critical' | 'warning' | 'info';

export interface DeliveryRule {
  id: string;
  triggerType: string;
  channelType: string;
  enabled: boolean;
  alertLevels: AlertLevel[];
}

interface DeliveryRulesProps {
  rules: DeliveryRule[];
  channels: string[];
  triggerTypes: string[];
  onAddRule?: (rule: DeliveryRule) => void;
  onUpdateRule?: (rule: DeliveryRule) => void;
  onRemoveRule?: (ruleId: string) => void;
}

const alertLevelColors: Record<AlertLevel, string> = {
  critical: 'text-red-600 bg-red-50',
  warning: 'text-yellow-600 bg-yellow-50',
  info: 'text-blue-600 bg-blue-50',
};

export function DeliveryRules({
  rules,
  channels,
  triggerTypes,
  onAddRule,
  onUpdateRule,
  onRemoveRule,
}: DeliveryRulesProps) {
  const [isAddingRule, setIsAddingRule] = useState(false);
  const [newRule, setNewRule] = useState({
    triggerType: triggerTypes[0] || '',
    channelType: channels[0] || '',
    alertLevels: ['critical', 'warning'] as AlertLevel[],
  });

  const handleAddRule = () => {
    if (!newRule.triggerType || !newRule.channelType) {
      return;
    }

    const rule: DeliveryRule = {
      id: `rule-${Date.now()}`,
      triggerType: newRule.triggerType,
      channelType: newRule.channelType,
      enabled: true,
      alertLevels: newRule.alertLevels,
    };

    onAddRule?.(rule);
    setNewRule({
      triggerType: triggerTypes[0] || '',
      channelType: channels[0] || '',
      alertLevels: ['critical', 'warning'],
    });
    setIsAddingRule(false);
  };

  const handleToggleRule = (rule: DeliveryRule) => {
    onUpdateRule?.({ ...rule, enabled: !rule.enabled });
  };

  const handleToggleAlertLevel = (rule: DeliveryRule, level: AlertLevel) => {
    const newLevels = rule.alertLevels.includes(level)
      ? rule.alertLevels.filter((l) => l !== level)
      : [...rule.alertLevels, level];

    onUpdateRule?.({ ...rule, alertLevels: newLevels });
  };

  const handleToggleNewRuleLevel = (level: AlertLevel) => {
    setNewRule((prev) => ({
      ...prev,
      alertLevels: prev.alertLevels.includes(level)
        ? prev.alertLevels.filter((l) => l !== level)
        : [...prev.alertLevels, level],
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Delivery Rules</h2>
        <p className="text-gray-600 mb-4">
          Configure which alerts are sent to which channels based on trigger type and severity.
        </p>
      </div>

      {/* Rules List */}
      <div className="space-y-3">
        {rules.map((rule) => (
          <div key={rule.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={rule.enabled}
                  onChange={() => handleToggleRule(rule)}
                  className="rounded"
                />
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {rule.triggerType} → {rule.channelType}
                  </h3>
                  <p className="text-sm text-gray-600">Alert Levels:</p>
                </div>
              </div>
              <button
                onClick={() => onRemoveRule?.(rule.id)}
                className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
              >
                Remove
              </button>
            </div>

            {/* Alert Levels */}
            <div className="ml-8 flex flex-wrap gap-2">
              {(['critical', 'warning', 'info'] as AlertLevel[]).map((level) => (
                <button
                  key={level}
                  onClick={() => handleToggleAlertLevel(rule, level)}
                  disabled={!rule.enabled}
                  className={`px-2 py-1 rounded text-sm font-medium transition ${
                    rule.alertLevels.includes(level)
                      ? alertLevelColors[level]
                      : 'bg-gray-100 text-gray-400'
                  } ${!rule.enabled && 'opacity-50'}`}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Add Rule Form */}
      {!isAddingRule ? (
        <button
          onClick={() => setIsAddingRule(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Add Rule
        </button>
      ) : (
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Add Delivery Rule</h3>

          <div className="space-y-3">
            {/* Trigger Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trigger Type
              </label>
              <select
                value={newRule.triggerType}
                onChange={(e) => setNewRule({ ...newRule, triggerType: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              >
                {triggerTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Channel Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Deliver To
              </label>
              <select
                value={newRule.channelType}
                onChange={(e) => setNewRule({ ...newRule, channelType: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded"
              >
                {channels.map((channel) => (
                  <option key={channel} value={channel}>
                    {channel}
                  </option>
                ))}
              </select>
            </div>

            {/* Alert Levels */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alert Levels
              </label>
              <div className="flex gap-2">
                {(['critical', 'warning', 'info'] as AlertLevel[]).map((level) => (
                  <button
                    key={level}
                    onClick={() => handleToggleNewRuleLevel(level)}
                    className={`px-3 py-1 rounded text-sm font-medium transition ${
                      newRule.alertLevels.includes(level)
                        ? alertLevelColors[level]
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleAddRule}
                disabled={!newRule.triggerType || !newRule.channelType}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Add Rule
              </button>
              <button
                onClick={() => {
                  setIsAddingRule(false);
                  setNewRule({
                    triggerType: triggerTypes[0] || '',
                    channelType: channels[0] || '',
                    alertLevels: ['critical', 'warning'],
                  });
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
