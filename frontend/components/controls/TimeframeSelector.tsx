'use client';

import { memo } from 'react';
import { useAnalysisStore } from '@/store/analysisStore';
import type { Timeframe, TimeframeOption } from '@/types';

interface TimeframeSelectorProps {
  onSelect?: (timeframe: Timeframe) => void;
}

const timeframeOptions: TimeframeOption[] = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: '1D' },
];

function TimeframeSelectorComponent({ onSelect }: TimeframeSelectorProps) {
  const { selectedTimeframe, setSelectedTimeframe } = useAnalysisStore();

  const handleSelect = (timeframe: Timeframe) => {
    setSelectedTimeframe(timeframe);
    onSelect?.(timeframe);
  };

  return (
    <div className="flex items-center gap-1 rounded-lg bg-slate-800 p-1">
      {timeframeOptions.map((option) => (
        <button
          key={option.value}
          onClick={() => handleSelect(option.value)}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            selectedTimeframe === option.value
              ? 'bg-slate-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-700'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export const TimeframeSelector = memo(TimeframeSelectorComponent);
