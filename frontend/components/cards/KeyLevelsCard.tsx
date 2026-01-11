'use client';

import { memo } from 'react';
import { Layers } from 'lucide-react';
import type { KeyLevels } from '@/types';

interface KeyLevelsCardProps {
  data: KeyLevels | undefined;
  currentPrice?: number;
  loading?: boolean;
}

function KeyLevelsCardComponent({ data, currentPrice, loading }: KeyLevelsCardProps) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-lg bg-slate-800 p-4">
        <div className="h-4 w-24 rounded bg-slate-700" />
        <div className="mt-3 h-8 w-32 rounded bg-slate-700" />
        <div className="mt-2 h-3 w-20 rounded bg-slate-700" />
      </div>
    );
  }

  if (!data) return null;

  // Calculate price position in value area
  const valueAreaRange = data.value_area_high - data.value_area_low;
  const pricePosition = currentPrice
    ? ((currentPrice - data.value_area_low) / valueAreaRange) * 100
    : 50;

  const priceInValueArea = currentPrice
    ? currentPrice >= data.value_area_low && currentPrice <= data.value_area_high
    : false;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          Key Levels
        </span>
        <Layers className="h-4 w-4 text-cyan-400" />
      </div>

      <div className="mt-3 space-y-3">
        {/* Value Area High */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-red-400" />
            <span className="text-sm text-slate-400">Value High</span>
          </div>
          <span className="font-mono text-sm text-slate-300">
            ${data.value_area_high.toLocaleString()}
          </span>
        </div>

        {/* POC */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-yellow-400" />
            <span className="text-sm text-slate-400">POC</span>
          </div>
          <span className="font-mono text-sm font-medium text-yellow-400">
            ${data.poc.toLocaleString()}
          </span>
        </div>

        {/* Value Area Low */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-400" />
            <span className="text-sm text-slate-400">Value Low</span>
          </div>
          <span className="font-mono text-sm text-slate-300">
            ${data.value_area_low.toLocaleString()}
          </span>
        </div>

        {/* Visual representation */}
        <div className="mt-3 pt-3 border-t border-slate-700">
          <div className="relative h-20 w-full rounded bg-slate-700/50">
            {/* Value Area */}
            <div
              className="absolute left-0 w-full bg-cyan-400/20 border-y border-cyan-400/30"
              style={{
                top: '20%',
                height: '60%',
              }}
            />

            {/* POC line */}
            <div
              className="absolute left-0 w-full h-0.5 bg-yellow-400"
              style={{ top: '50%' }}
            />

            {/* Current price marker */}
            {currentPrice && (
              <div
                className={`absolute left-0 w-full h-0.5 ${
                  priceInValueArea ? 'bg-white' : 'bg-orange-400'
                }`}
                style={{
                  top: `${Math.max(5, Math.min(95, 100 - pricePosition * 0.6 - 20))}%`,
                }}
              >
                <span className="absolute -right-1 -top-3 text-[10px] text-slate-300">
                  Current
                </span>
              </div>
            )}

            {/* Labels */}
            <span className="absolute top-1 right-2 text-[10px] text-slate-500">VAH</span>
            <span className="absolute top-1/2 -translate-y-1/2 right-2 text-[10px] text-yellow-400">POC</span>
            <span className="absolute bottom-1 right-2 text-[10px] text-slate-500">VAL</span>
          </div>

          <div className="mt-2 text-center text-xs text-slate-500">
            {priceInValueArea ? (
              <span className="text-cyan-400">Price in Value Area</span>
            ) : currentPrice && currentPrice > data.value_area_high ? (
              <span className="text-red-400">Price above Value Area</span>
            ) : (
              <span className="text-green-400">Price below Value Area</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export const KeyLevelsCard = memo(KeyLevelsCardComponent);
