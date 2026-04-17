/**
 * Reusable multi-select dropdown component
 */

import React, { useState, useRef, useEffect } from "react";

interface MultiSelectProps {
  label: string;
  placeholder?: string;
  options: string[];
  selected: string[] | null;
  onChange: (selected: string[] | null) => void;
  disabled?: boolean;
}

export const MultiSelect: React.FC<MultiSelectProps> = ({
  label,
  placeholder = "Select options...",
  options,
  selected,
  onChange,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedArray = selected || [];
  const displayText = selectedArray.length > 0
    ? `${selectedArray.length} selected`
    : placeholder;

  const handleToggleOption = (option: string) => {
    const newSelected = selectedArray.includes(option)
      ? selectedArray.filter(item => item !== option)
      : [...selectedArray, option];

    onChange(newSelected.length > 0 ? newSelected : null);
  };

  const handleSelectAll = () => {
    onChange(options.length === selectedArray.length ? null : options);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(null);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
          className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-left text-sm flex items-center justify-between hover:bg-gray-50 disabled:bg-gray-100"
        >
          <span className="text-gray-700">{displayText}</span>
          <div className="flex items-center gap-2">
            {selectedArray.length > 0 && (
              <button
                onClick={handleClear}
                className="p-1 hover:bg-gray-200 rounded"
              >
                ✕
              </button>
            )}
            <svg
              className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
            {/* Select All */}
            <div className="px-4 py-2 border-b">
              <button
                onClick={handleSelectAll}
                className="text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                {options.length === selectedArray.length ? "Deselect All" : "Select All"}
              </button>
            </div>

            {/* Options */}
            <div className="max-h-64 overflow-y-auto">
              {options.map(option => (
                <label
                  key={option}
                  className="flex items-center px-4 py-3 hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedArray.includes(option)}
                    onChange={() => handleToggleOption(option)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="ml-3 text-sm text-gray-700">{option}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiSelect;
