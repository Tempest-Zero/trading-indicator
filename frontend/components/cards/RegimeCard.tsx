'use client';

import { memo } from 'react';
import { TrendingUp, RefreshCcw, HelpCircle } from 'lucide-react';
import type { RegimeData } from '@/types';

interface RegimeCardProps {
  data: RegimeData | undefined;
  loading?: boolean;
}

const regimeConfig = {
  TRENDING: {
    icon: TrendingUp,
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    borderColor: 'border-green-400/30',
    label: 'Trending',
  },
  MEAN_REVERTING: {
    icon: RefreshCcw,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    borderColor: 'border-blue-400/30',
    label: 'Mean Reverting',
  },
  RANDOM_WALK: {
    icon: HelpCircle,
    color: 'text-slate-400',
    bgColor: 'bg-slate-400/10',
    borderColor: 'border-slate-400/30',
    label: 'Random Walk',
  },
  UNKNOWN: {
    icon: HelpCircle,
    color: 'text-slate-400',
    bgColor: 'bg-slate-400/10',
    borderColor: 'border-slate-400/30',
    label: 'Unknown',
  },
};

function RegimeCardComponent({ data, loading }: RegimeCardProps) {
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

  const config = regimeConfig[data.regime] || regimeConfig.UNKNOWN;
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border ${config.borderColor} ${config.bgColor} p-4`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          Market Regime
        </span>
        <Icon className={`h-4 w-4 ${config.color}`} />
      </div>

      <div className="mt-2">
        <div className={`text-xl font-bold ${config.color}`}>{config.label}</div>
        <div className="mt-1 text-sm text-slate-400">{data.description}</div>
      </div>

      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Hurst Value</span>
          <span className="font-mono text-slate-300">{data.hurst_value.toFixed(3)}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Confidence</span>
          <span className="font-mono text-slate-300">{(data.confidence * 100).toFixed(0)}%</span>
        </div>

        {/* Hurst gauge */}
        <div className="mt-2">
          <div className="h-1.5 w-full rounded-full bg-slate-700">
            <div
              className={`h-full rounded-full transition-all ${
                data.hurst_value > 0.5 ? 'bg-green-400' : 'bg-blue-400'
              }`}
              style={{ width: `${data.hurst_value * 100}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-slate-500">
            <span>Mean Revert</span>
            <span>0.5</span>
            <span>Trending</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export const RegimeCard = memo(RegimeCardComponent);
