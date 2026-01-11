// React Query hooks for analysis data

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getAnalysis, getChartData, getSymbols } from '@/lib/api';
import type { FullAnalysis, ChartData, SymbolCategory } from '@/types';

// Query keys
export const queryKeys = {
  analysis: (symbol: string, timeframe: string) => ['analysis', symbol, timeframe] as const,
  chartData: (symbol: string, timeframe: string) => ['chartData', symbol, timeframe] as const,
  symbols: ['symbols'] as const,
};

// Analysis hook
export function useAnalysis(symbol: string, timeframe: string = '1h', enabled: boolean = true) {
  return useQuery<FullAnalysis, Error>({
    queryKey: queryKeys.analysis(symbol, timeframe),
    queryFn: () => getAnalysis(symbol, timeframe),
    enabled: enabled && !!symbol,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
}

// Chart data hook
export function useChartData(symbol: string, timeframe: string = '1h', enabled: boolean = true) {
  return useQuery<ChartData, Error>({
    queryKey: queryKeys.chartData(symbol, timeframe),
    queryFn: () => getChartData(symbol, timeframe),
    enabled: enabled && !!symbol,
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

// Symbols hook
export function useSymbols() {
  return useQuery<SymbolCategory, Error>({
    queryKey: queryKeys.symbols,
    queryFn: getSymbols,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Prefetch hook for watchlist
export function usePrefetchAnalysis() {
  const queryClient = useQueryClient();

  return (symbol: string, timeframe: string = '1h') => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.analysis(symbol, timeframe),
      queryFn: () => getAnalysis(symbol, timeframe),
      staleTime: 30000,
    });
  };
}

// Invalidate analysis (force refresh)
export function useInvalidateAnalysis() {
  const queryClient = useQueryClient();

  return (symbol?: string, timeframe?: string) => {
    if (symbol && timeframe) {
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis(symbol, timeframe) });
      queryClient.invalidateQueries({ queryKey: queryKeys.chartData(symbol, timeframe) });
    } else {
      queryClient.invalidateQueries({ queryKey: ['analysis'] });
      queryClient.invalidateQueries({ queryKey: ['chartData'] });
    }
  };
}
