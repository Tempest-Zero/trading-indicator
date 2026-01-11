'use client';

import { useEffect, useCallback, useState } from 'react';
import { useAnalysisStore } from '@/store/analysisStore';
import { useAnalysis, useChartData, useWebSocket } from '@/hooks';

// Charts
import { PriceChart, ZScoreChart, VolumeChart, HurstChart } from './charts';

// Cards
import { RegimeCard, TrendCard, StatsCard, KeyLevelsCard, ActionCard } from './cards';

// Controls
import { SymbolSelector, TimeframeSelector, ConnectionStatus, Watchlist } from './controls';

export function Dashboard() {
  const { selectedSymbol, selectedTimeframe, sidebarOpen, updateLiveAnalysis } = useAnalysisStore();
  const [clientId] = useState(() => `client_${Date.now()}`);

  // Fetch analysis and chart data
  const {
    data: analysis,
    isLoading: analysisLoading,
    error: analysisError,
  } = useAnalysis(selectedSymbol, selectedTimeframe);

  const {
    data: chartData,
    isLoading: chartLoading,
  } = useChartData(selectedSymbol, selectedTimeframe);

  // WebSocket connection
  const handleMessage = useCallback(
    (data: any) => {
      updateLiveAnalysis(data);
    },
    [updateLiveAnalysis]
  );

  const { status, lastUpdate, subscribe, unsubscribe } = useWebSocket({
    clientId,
    onMessage: handleMessage,
    autoReconnect: true,
  });

  // Subscribe to selected symbol
  useEffect(() => {
    if (selectedSymbol) {
      subscribe([selectedSymbol]);
    }
    return () => {
      if (selectedSymbol) {
        unsubscribe([selectedSymbol]);
      }
    };
  }, [selectedSymbol, subscribe, unsubscribe]);

  const isLoading = analysisLoading || chartLoading;

  return (
    <div className="flex h-screen bg-slate-950">
      {/* Sidebar - Watchlist */}
      {sidebarOpen && (
        <div className="w-64 border-r border-slate-800 p-4">
          <Watchlist />
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b border-slate-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-white">Quant Analysis</h1>
              <SymbolSelector />
              <TimeframeSelector />
            </div>

            <div className="flex items-center gap-4">
              {/* Current price */}
              {analysis && (
                <div className="text-right">
                  <div className="text-xs text-slate-500">Current Price</div>
                  <div className="text-lg font-bold text-white font-mono">
                    ${analysis.current_price.toLocaleString()}
                  </div>
                </div>
              )}

              <ConnectionStatus status={status} lastUpdate={lastUpdate} />
            </div>
          </div>
        </header>

        {/* Main grid */}
        <main className="flex-1 overflow-auto p-6">
          {analysisError ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-red-400 text-lg mb-2">Error loading analysis</div>
                <div className="text-slate-500">{analysisError.message}</div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-12 gap-4">
              {/* Charts - Left side */}
              <div className="col-span-8 space-y-4">
                {/* Price chart */}
                <PriceChart data={chartData} height={400} showKalman />

                {/* Indicator charts */}
                <div className="grid grid-cols-3 gap-4">
                  <ZScoreChart data={chartData} height={120} />
                  <HurstChart data={chartData} height={120} />
                  <VolumeChart data={chartData} height={120} />
                </div>
              </div>

              {/* Analysis cards - Right side */}
              <div className="col-span-4 space-y-4">
                {/* Action card - Most important */}
                <ActionCard analysis={analysis} loading={isLoading} />

                {/* Grid of smaller cards */}
                <div className="grid grid-cols-2 gap-4">
                  <RegimeCard data={analysis?.regime} loading={isLoading} />
                  <TrendCard
                    data={analysis?.trend}
                    currentPrice={analysis?.current_price}
                    loading={isLoading}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <StatsCard data={analysis?.statistical} loading={isLoading} />
                  <KeyLevelsCard
                    data={analysis?.key_levels}
                    currentPrice={analysis?.current_price}
                    loading={isLoading}
                  />
                </div>

                {/* Analysis notes */}
                {analysis?.notes && analysis.notes.length > 3 && (
                  <div className="rounded-lg bg-slate-800/50 p-4">
                    <h3 className="text-sm font-medium text-slate-400 mb-2">Additional Notes</h3>
                    <ul className="space-y-1">
                      {analysis.notes.slice(3).map((note, i) => (
                        <li key={i} className="text-xs text-slate-500 flex items-start gap-2">
                          <span className="text-slate-600">•</span>
                          {note}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-800 px-6 py-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Quant Market Analysis Engine</span>
            <span>
              {analysis?.timestamp &&
                `Last analysis: ${new Date(analysis.timestamp).toLocaleString()}`}
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
