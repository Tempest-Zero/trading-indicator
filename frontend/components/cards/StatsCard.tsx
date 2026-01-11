'use client';

import { memo } from 'react';
import { BarChart3 } from 'lucide-react';
import type { StatisticalData } from '@/types';

interface StatsCardProps {
  data: StatisticalData | undefined;
  loading?: boolean;
}

function getZScoreColor(zscore: number): string {
  if (zscore > 2) return 'text-red-400';
  if (zscore > 1) return 'text-orange-400';
  if (zscore < -2) return 'text-green-400';
  if (zscore < -1) return 'text-emerald-400';
  return 'text-slate-300';
}

function getConditionColor(condition: string): string {
  const lower = condition.toLowerCase();
  if (lower.includes('oversold') || lower.includes('undervalued')) return 'text-green-400';
  if (lower.includes('overbought') || lower.includes('overvalued')) return 'text-red-400';
  return 'text-slate-400';
}

function StatsCardComponent({ data, loading }: StatsCardProps) {
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

  const zscoreColor = getZScoreColor(data.zscore);

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          Statistical Position
        </span>
        <BarChart3 className="h-4 w-4 text-purple-400" />
      </div>

      <div className="mt-2">
        <div className={`text-2xl font-bold font-mono ${zscoreColor}`}>
          {data.zscore >= 0 ? '+' : ''}{data.zscore.toFixed(2)}σ
        </div>
        <div className={`mt-1 text-sm ${getConditionColor(data.condition)}`}>
          {data.condition}
        </div>
      </div>

      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-500">Percentile</span>
          <span className="font-mono text-slate-300">{data.percentile.toFixed(0)}%</span>
        </div>

        {/* Z-Score gauge */}
        <div className="mt-2">
          <div className="relative h-2 w-full rounded-full bg-slate-700">
            {/* Colored zones */}
            <div className="absolute left-0 top-0 h-full w-[20%] rounded-l-full bg-green-400/30" />
            <div className="absolute right-0 top-0 h-full w-[20%] rounded-r-full bg-red-400/30" />
            {/* Marker */}
            <div
              className={`absolute top-1/2 h-3 w-1 -translate-y-1/2 rounded-full ${
                data.zscore > 2 ? 'bg-red-400' : data.zscore < -2 ? 'bg-green-400' : 'bg-slate-300'
              }`}
              style={{
                left: `${Math.max(0, Math.min(100, (data.zscore + 3) / 6 * 100))}%`,
              }}
            />
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-slate-500">
            <span>-3σ</span>
            <span>0</span>
            <span>+3σ</span>
          </div>
        </div>

        {/* Percentile bar */}
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Historical Rank</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-slate-700">
            <div
              className="h-full rounded-full bg-purple-400 transition-all"
              style={{ width: `${data.percentile}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export const StatsCard = memo(StatsCardComponent);
