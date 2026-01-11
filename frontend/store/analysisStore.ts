// Zustand store for analysis state

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Timeframe, FullAnalysis } from '@/types';

interface AnalysisState {
  // Selection
  selectedSymbol: string;
  selectedTimeframe: Timeframe;

  // Watchlist
  watchlist: string[];

  // UI state
  sidebarOpen: boolean;
  chartHeight: number;

  // Real-time data cache
  liveAnalysis: Record<string, FullAnalysis>;

  // Actions
  setSelectedSymbol: (symbol: string) => void;
  setSelectedTimeframe: (timeframe: Timeframe) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  toggleSidebar: () => void;
  setChartHeight: (height: number) => void;
  updateLiveAnalysis: (analysis: FullAnalysis) => void;
  clearLiveAnalysis: () => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set, get) => ({
      // Default state
      selectedSymbol: 'BTC/USDT',
      selectedTimeframe: '1h',
      watchlist: ['BTC/USDT', 'ETH/USDT', 'AAPL', 'SPY'],
      sidebarOpen: true,
      chartHeight: 400,
      liveAnalysis: {},

      // Actions
      setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

      setSelectedTimeframe: (timeframe) => set({ selectedTimeframe: timeframe }),

      addToWatchlist: (symbol) =>
        set((state) => ({
          watchlist: state.watchlist.includes(symbol)
            ? state.watchlist
            : [...state.watchlist, symbol],
        })),

      removeFromWatchlist: (symbol) =>
        set((state) => ({
          watchlist: state.watchlist.filter((s) => s !== symbol),
        })),

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      setChartHeight: (height) => set({ chartHeight: height }),

      updateLiveAnalysis: (analysis) =>
        set((state) => ({
          liveAnalysis: {
            ...state.liveAnalysis,
            [analysis.symbol]: analysis,
          },
        })),

      clearLiveAnalysis: () => set({ liveAnalysis: {} }),
    }),
    {
      name: 'quant-analysis-storage',
      partialize: (state) => ({
        selectedSymbol: state.selectedSymbol,
        selectedTimeframe: state.selectedTimeframe,
        watchlist: state.watchlist,
        sidebarOpen: state.sidebarOpen,
        chartHeight: state.chartHeight,
      }),
    }
  )
);

// Selectors
export const selectSelectedSymbol = (state: AnalysisState) => state.selectedSymbol;
export const selectSelectedTimeframe = (state: AnalysisState) => state.selectedTimeframe;
export const selectWatchlist = (state: AnalysisState) => state.watchlist;
export const selectSidebarOpen = (state: AnalysisState) => state.sidebarOpen;
export const selectLiveAnalysis = (symbol: string) => (state: AnalysisState) =>
  state.liveAnalysis[symbol];
