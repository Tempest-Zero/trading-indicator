'use client';

import { memo } from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import type { TrendData } from '@/types';

interface TrendCardProps {
  data: TrendData | undefined;
  currentPrice?: number;
  loading?: boolean;
}

const trendConfig = {
  UP: {
    icon: ArrowUpRight,
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    borderColor: 'border-green-400/30',
    label: 'Bullish',
  },
  DOWN: {
    icon: ArrowDownRight,
    color: 'text-red-400',
    bgColor: 'bg-red-400/10',
    borderColor: 'border-red-400/30',
    label: 'Bearish',
  },
  NEUTRAL: {
    icon: Minus,
    color: 'text-slate-400',
    bgColor: 'bg-slate-400/10',
    borderColor: 'border-slate-400/30',
    label: 'Neutral',
  },
};

function TrendCardComponent({ data, currentPrice, loading }: TrendCardProps) {
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

  const config = trendConfig[data.direction] || trendConfig.NEUTRAL;
  const Icon = config.icon;

  // Calculate distance from Kalman
  const kalmanDiff = currentPrice ? ((currentPrice - data.kalman_price) / data.kalman_price) * 100 : 0;

  return (
    <div className={`rounded-lg border ${config.borderColor} ${config.bgColor} p-4`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          Trend Direction
        </span>
        <Icon className={`h-4 w-4 ${config.color}`} />
      </div>

      <div className="mt-2">
        <div className={`text-xl font-bold ${config.color}`}>{config.label}</div>
      </div>

      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Kalman Price</span>
          <span className="font-mono text-slate-300">${data.kalman_price.toLocaleString()}</span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Distance</span>
          <span className={`font-mono ${kalmanDiff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {kalmanDiff >= 0 ? '+' : ''}{kalmanDiff.toFixed(2)}%
          </span>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Velocity</span>
          <span className={`font-mono ${data.velocity >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {data.velocity >= 0 ? '+' : ''}{data.velocity.toFixed(4)}
          </span>
        </div>

        {/* Velocity indicator */}
        <div className="mt-2">
          <div className="relative h-1.5 w-full rounded-full bg-slate-700">
            <div className="absolute left-1/2 top-0 h-full w-0.5 bg-slate-500" />
            <div
              className={`absolute top-0 h-full rounded-full transition-all ${
                data.velocity >= 0 ? 'bg-green-400' : 'bg-red-400'
              }`}
              style={{
                left: data.velocity >= 0 ? '50%' : `${50 - Math.min(Math.abs(data.velocity) * 5000, 50)}%`,
                width: `${Math.min(Math.abs(data.velocity) * 5000, 50)}%`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export const TrendCard = memo(TrendCardComponent);
