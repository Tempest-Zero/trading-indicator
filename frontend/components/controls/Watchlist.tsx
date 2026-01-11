'use client';

import { useState, memo } from 'react';
import { Plus, X, Star, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useAnalysisStore } from '@/store/analysisStore';
import { useAnalysis } from '@/hooks';

interface WatchlistItemProps {
  symbol: string;
  isSelected: boolean;
  onSelect: () => void;
  onRemove: () => void;
}

function WatchlistItem({ symbol, isSelected, onSelect, onRemove }: WatchlistItemProps) {
  const { data: analysis, isLoading } = useAnalysis(symbol, '1h');

  const getBiasIcon = () => {
    if (!analysis) return <Minus className="h-3 w-3 text-slate-500" />;
    switch (analysis.suggested_bias) {
      case 'UP':
        return <TrendingUp className="h-3 w-3 text-green-400" />;
      case 'DOWN':
        return <TrendingDown className="h-3 w-3 text-red-400" />;
      default:
        return <Minus className="h-3 w-3 text-slate-400" />;
    }
  };

  return (
    <div
      className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isSelected ? 'bg-slate-700' : 'hover:bg-slate-800'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-2 min-w-0">
        {getBiasIcon()}
        <span className={`text-sm truncate ${isSelected ? 'text-white' : 'text-slate-300'}`}>
          {symbol}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {analysis && (
          <span className={`text-xs font-mono ${
            analysis.suggested_bias === 'UP' ? 'text-green-400' :
            analysis.suggested_bias === 'DOWN' ? 'text-red-400' :
            'text-slate-400'
          }`}>
            {(analysis.confidence * 100).toFixed(0)}%
          </span>
        )}
        {isLoading && (
          <div className="h-3 w-3 rounded-full border-2 border-slate-500 border-t-transparent animate-spin" />
        )}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-600 rounded transition-opacity"
        >
          <X className="h-3 w-3 text-slate-400" />
        </button>
      </div>
    </div>
  );
}

function WatchlistComponent() {
  const [newSymbol, setNewSymbol] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const {
    watchlist,
    selectedSymbol,
    setSelectedSymbol,
    addToWatchlist,
    removeFromWatchlist,
  } = useAnalysisStore();

  const handleAdd = () => {
    if (newSymbol.trim()) {
      addToWatchlist(newSymbol.trim().toUpperCase());
      setNewSymbol('');
      setIsAdding(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAdd();
    } else if (e.key === 'Escape') {
      setIsAdding(false);
      setNewSymbol('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-lg border border-slate-800">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Star className="h-4 w-4 text-yellow-400" />
          <span className="text-sm font-medium text-white">Watchlist</span>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="p-1 hover:bg-slate-700 rounded transition-colors"
        >
          <Plus className="h-4 w-4 text-slate-400" />
        </button>
      </div>

      {/* Add symbol input */}
      {isAdding && (
        <div className="px-3 py-2 border-b border-slate-800">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add symbol (e.g., BTC/USDT)"
            className="w-full bg-slate-800 rounded px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-600"
            autoFocus
          />
        </div>
      )}

      {/* Symbol list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {watchlist.length === 0 ? (
          <div className="text-center text-slate-500 py-4 text-sm">
            No symbols in watchlist
          </div>
        ) : (
          watchlist.map((symbol) => (
            <WatchlistItem
              key={symbol}
              symbol={symbol}
              isSelected={symbol === selectedSymbol}
              onSelect={() => setSelectedSymbol(symbol)}
              onRemove={() => removeFromWatchlist(symbol)}
            />
          ))
        )}
      </div>
    </div>
  );
}

export const Watchlist = memo(WatchlistComponent);
