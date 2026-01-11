'use client';

import { useState, useRef, useEffect, memo } from 'react';
import { Search, ChevronDown, Bitcoin, DollarSign, BarChart2, X } from 'lucide-react';
import { useSymbols } from '@/hooks';
import { useAnalysisStore } from '@/store/analysisStore';

interface SymbolSelectorProps {
  onSelect?: (symbol: string) => void;
}

function SymbolSelectorComponent({ onSelect }: SymbolSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { selectedSymbol, setSelectedSymbol } = useAnalysisStore();
  const { data: symbols, isLoading } = useSymbols();

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter symbols
  const filterSymbols = (list: string[] | undefined) => {
    if (!list) return [];
    if (!search) return list;
    return list.filter((s) => s.toLowerCase().includes(search.toLowerCase()));
  };

  const handleSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    onSelect?.(symbol);
    setIsOpen(false);
    setSearch('');
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'crypto':
        return <Bitcoin className="h-3 w-3" />;
      case 'stocks':
        return <DollarSign className="h-3 w-3" />;
      case 'indices':
        return <BarChart2 className="h-3 w-3" />;
      default:
        return null;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selected display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-white hover:bg-slate-700 transition-colors"
      >
        <span className="font-medium">{selectedSymbol}</span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-72 rounded-lg bg-slate-800 border border-slate-700 shadow-xl z-50">
          {/* Search */}
          <div className="p-2 border-b border-slate-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search symbols..."
                className="w-full bg-slate-900 rounded-md pl-9 pr-8 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-600"
                autoFocus
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Symbol lists */}
          <div className="max-h-80 overflow-y-auto p-2">
            {isLoading ? (
              <div className="text-center text-slate-500 py-4">Loading symbols...</div>
            ) : (
              <>
                {/* Crypto */}
                {filterSymbols(symbols?.crypto).length > 0 && (
                  <div className="mb-2">
                    <div className="flex items-center gap-2 px-2 py-1 text-xs text-slate-500 uppercase tracking-wider">
                      {getCategoryIcon('crypto')}
                      Crypto
                    </div>
                    {filterSymbols(symbols?.crypto).map((symbol) => (
                      <button
                        key={symbol}
                        onClick={() => handleSelect(symbol)}
                        className={`w-full text-left px-3 py-2 rounded text-sm hover:bg-slate-700 transition-colors ${
                          symbol === selectedSymbol ? 'bg-slate-700 text-white' : 'text-slate-300'
                        }`}
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                )}

                {/* Stocks */}
                {filterSymbols(symbols?.stocks).length > 0 && (
                  <div className="mb-2">
                    <div className="flex items-center gap-2 px-2 py-1 text-xs text-slate-500 uppercase tracking-wider">
                      {getCategoryIcon('stocks')}
                      Stocks
                    </div>
                    {filterSymbols(symbols?.stocks).map((symbol) => (
                      <button
                        key={symbol}
                        onClick={() => handleSelect(symbol)}
                        className={`w-full text-left px-3 py-2 rounded text-sm hover:bg-slate-700 transition-colors ${
                          symbol === selectedSymbol ? 'bg-slate-700 text-white' : 'text-slate-300'
                        }`}
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                )}

                {/* Indices */}
                {filterSymbols(symbols?.indices).length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 px-2 py-1 text-xs text-slate-500 uppercase tracking-wider">
                      {getCategoryIcon('indices')}
                      Indices
                    </div>
                    {filterSymbols(symbols?.indices).map((symbol) => (
                      <button
                        key={symbol}
                        onClick={() => handleSelect(symbol)}
                        className={`w-full text-left px-3 py-2 rounded text-sm hover:bg-slate-700 transition-colors ${
                          symbol === selectedSymbol ? 'bg-slate-700 text-white' : 'text-slate-300'
                        }`}
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export const SymbolSelector = memo(SymbolSelectorComponent);
