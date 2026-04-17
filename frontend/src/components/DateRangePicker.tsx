/**
 * Date range picker component
 */

import React, { useState } from "react";

interface DateRangePickerProps {
  label: string;
  startDate: string;
  endDate: string;
  onChange: (start: string, end: string) => void;
  onClear?: () => void;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  label,
  startDate,
  endDate,
  onChange,
  onClear,
}) => {
  const [localStart, setLocalStart] = useState<string>(startDate);
  const [localEnd, setLocalEnd] = useState<string>(endDate);

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newStart = e.target.value;
    setLocalStart(newStart);
    if (newStart && localEnd) {
      onChange(newStart, localEnd);
    }
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnd = e.target.value;
    setLocalEnd(newEnd);
    if (localStart && newEnd) {
      onChange(localStart, newEnd);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        {onClear && (
          <button
            onClick={onClear}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            Clear
          </button>
        )}
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Start Date</p>
          <input
            type="date"
            value={localStart}
            onChange={handleStartChange}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          />
        </div>
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">End Date</p>
          <input
            type="date"
            value={localEnd}
            onChange={handleEndChange}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          />
        </div>
      </div>

      {localStart && localEnd && (
        <p className="text-xs text-gray-600 text-center">
          {new Date(localStart).toLocaleDateString()} → {new Date(localEnd).toLocaleDateString()}
        </p>
      )}
    </div>
  );
};

export default DateRangePicker;
