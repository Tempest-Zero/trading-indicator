'use client';

import { useEffect, useRef, memo } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, ColorType } from 'lightweight-charts';
import type { ChartData } from '@/types';

interface PriceChartProps {
  data: ChartData | undefined;
  height?: number;
  showKalman?: boolean;
}

function PriceChartComponent({ data, height = 400, showKalman = true }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const kalmanSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // Initialize chart
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: containerRef.current.clientWidth,
      height,
      crosshair: {
        mode: 1,
        vertLine: { color: '#475569', width: 1, style: 2 },
        horzLine: { color: '#475569', width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: '#1e293b',
      },
      timeScale: {
        borderColor: '#1e293b',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    // Kalman filter line
    const kalmanSeries = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    kalmanSeriesRef.current = kalmanSeries;

    // Handle resize
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height]);

  // Update data
  useEffect(() => {
    if (!data || !candleSeriesRef.current || !kalmanSeriesRef.current) return;

    // Format candlestick data
    const candleData: CandlestickData[] = data.ohlcv.map((bar) => ({
      time: bar.timestamp.split('T')[0] as string,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    candleSeriesRef.current.setData(candleData);

    // Format Kalman line data
    if (showKalman && data.kalman_line.length > 0) {
      const kalmanData: LineData[] = data.ohlcv.map((bar, i) => ({
        time: bar.timestamp.split('T')[0] as string,
        value: data.kalman_line[i] ?? bar.close,
      }));
      kalmanSeriesRef.current.setData(kalmanData);
    }

    // Fit content
    chartRef.current?.timeScale().fitContent();
  }, [data, showKalman]);

  return (
    <div className="relative rounded-lg bg-slate-900 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-300">Price Chart</h3>
        {showKalman && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="inline-block h-0.5 w-4 bg-amber-500" />
            Kalman Filter
          </div>
        )}
      </div>
      <div ref={containerRef} className="w-full" />
    </div>
  );
}

export const PriceChart = memo(PriceChartComponent);
