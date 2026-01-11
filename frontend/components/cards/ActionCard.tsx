'use client';

import { memo } from 'react';
import { Target, AlertCircle } from 'lucide-react';
import type { FullAnalysis } from '@/types';

interface ActionCardProps {
  analysis: FullAnalysis | undefined;
  loading?: boolean;
}

const biasConfig = {
  UP: {
    color: 'text-green-400',
    bgColor: 'bg-green-400',
    borderColor: 'border-green-400',
    label: 'LONG BIAS',
    description: 'Conditions favor bullish positions',
  },
  DOWN: {
    color: 'text-red-400',
    bgColor: 'bg-red-400',
    borderColor: 'border-red-400',
    label: 'SHORT BIAS',
    description: 'Conditions favor bearish positions',
  },
  NEUTRAL: {
    color: 'text-slate-400',
    bgColor: 'bg-slate-400',
    borderColor: 'border-slate-400',
    label: 'NEUTRAL',
    description: 'No clear directional bias',
  },
  WAIT: {
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-400',
    borderColor: 'border-yellow-400',
    label: 'WAIT',
    description: 'Conditions unfavorable, avoid trading',
  },
};

function ActionCardComponent({ analysis, loading }: ActionCardProps) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-lg bg-slate-800 p-6">
        <div className="h-6 w-32 rounded bg-slate-700" />
        <div className="mt-4 h-12 w-full rounded bg-slate-700" />
        <div className="mt-4 h-4 w-48 rounded bg-slate-700" />
      </div>
    );
  }

  if (!analysis) return null;

  const config = biasConfig[analysis.suggested_bias] || biasConfig.NEUTRAL;

  return (
    <div className={`rounded-lg border-2 ${config.borderColor} bg-slate-900 p-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className={`h-5 w-5 ${config.color}`} />
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Signal
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Confidence</span>
          <span className={`text-lg font-bold ${config.color}`}>
            {(analysis.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Main signal */}
      <div className="mt-4 text-center">
        <div className={`text-3xl font-bold ${config.color}`}>{config.label}</div>
        <div className="mt-1 text-sm text-slate-500">{config.description}</div>
      </div>

      {/* Probabilities */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-slate-800 p-3 text-center">
          <div className="text-xs text-slate-500">Pullback Prob</div>
          <div className="mt-1 text-xl font-bold text-orange-400">
            {(analysis.pullback_probability * 100).toFixed(0)}%
          </div>
        </div>
        <div className="rounded-lg bg-slate-800 p-3 text-center">
          <div className="text-xs text-slate-500">Continuation</div>
          <div className="mt-1 text-xl font-bold text-cyan-400">
            {(analysis.continuation_probability * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mt-4">
        <div className="h-2 w-full rounded-full bg-slate-700">
          <div
            className={`h-full rounded-full ${config.bgColor} transition-all`}
            style={{ width: `${analysis.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Notes */}
      {analysis.notes && analysis.notes.length > 0 && (
        <div className="mt-4 border-t border-slate-700 pt-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
            <AlertCircle className="h-3 w-3" />
            Analysis Notes
          </div>
          <ul className="space-y-1">
            {analysis.notes.slice(0, 3).map((note, i) => (
              <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                <span className="text-slate-600">•</span>
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export const ActionCard = memo(ActionCardComponent);
