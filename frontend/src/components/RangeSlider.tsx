/**
 * Range slider component for min/max filtering
 */

import React, { useState, useEffect } from "react";

interface RangeSliderProps {
  label: string;
  unit?: string;
  min: number;
  max: number;
  step?: number;
  value: [number, number] | null;
  onChange: (value: [number, number] | null) => void;
  onClear?: () => void;
}

export const RangeSlider: React.FC<RangeSliderProps> = ({
  label,
  unit = "",
  min,
  max,
  step = 1,
  value,
  onChange,
  onClear,
}) => {
  const [localMin, setLocalMin] = useState<number>(value?.[0] ?? min);
  const [localMax, setLocalMax] = useState<number>(value?.[1] ?? max);

  useEffect(() => {
    if (value) {
      setLocalMin(value[0]);
      setLocalMax(value[1]);
    }
  }, [value]);

  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMin = Math.min(parseFloat(e.target.value), localMax);
    setLocalMin(newMin);
    if (newMin !== min || localMax !== max) {
      onChange([newMin, localMax]);
    } else {
      onChange(null);
    }
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMax = Math.max(parseFloat(e.target.value), localMin);
    setLocalMax(newMax);
    if (localMin !== min || newMax !== max) {
      onChange([localMin, newMax]);
    } else {
      onChange(null);
    }
  };

  const handleClear = () => {
    setLocalMin(min);
    setLocalMax(max);
    onChange(null);
    onClear?.();
  };

  const isActive = value !== null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">{label}</label>
        {isActive && (
          <button
            onClick={handleClear}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            Reset
          </button>
        )}
      </div>

      {/* Display values */}
      <div className="flex gap-4">
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Min</p>
          <input
            type="number"
            value={localMin}
            onChange={handleMinChange}
            min={min}
            max={localMax}
            step={step}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          />
        </div>
        <div className="flex-1">
          <p className="text-xs text-gray-600 mb-1">Max</p>
          <input
            type="number"
            value={localMax}
            onChange={handleMaxChange}
            min={localMin}
            max={max}
            step={step}
            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          />
        </div>
      </div>

      {/* Visual sliders */}
      <div className="space-y-2">
        <input
          type="range"
          value={localMin}
          onChange={handleMinChange}
          min={min}
          max={max}
          step={step}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <input
          type="range"
          value={localMax}
          onChange={handleMaxChange}
          min={min}
          max={max}
          step={step}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Display range text */}
      <p className="text-xs text-gray-600 text-center">
        {localMin} {unit} - {localMax} {unit}
      </p>
    </div>
  );
};

export default RangeSlider;
