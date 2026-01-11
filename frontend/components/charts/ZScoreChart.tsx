'use client';

import { useEffect, useRef, memo } from 'react';
import { createChart, IChartApi, ISeriesApi, HistogramData, ColorType } from 'lightweight-charts';
import type { ChartData } from '@/types';

interface ZScoreChartProps {
  data: ChartData | undefined;
  height?: number;
}

function ZScoreChartComponent({ data, height = 150 }: ZScoreChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

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
      rightPriceScale: {
        borderColor: '#1e293b',
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: '#1e293b',
        visible: false,
      },
      crosshair: {
        mode: 0,
      },
    });

    // Histogram series for Z-Score
    const series = chart.addHistogramSeries({
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;

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
    if (!data || !seriesRef.current) return;

    // Format Z-Score histogram data with color based on value
    const histData: HistogramData[] = data.ohlcv.map((bar, i) => {
      const zscore = data.zscore_series[i] ?? 0;
      let color = '#64748b'; // neutral gray

      if (zscore > 2) color = '#ef4444'; // overbought - red
      else if (zscore > 1) color = '#f97316'; // high - orange
      else if (zscore < -2) color = '#22c55e'; // oversold - green
      else if (zscore < -1) color = '#10b981'; // low - emerald

      return {
        time: bar.timestamp.split('T')[0] as string,
        value: zscore,
        color,
      };
    });

    seriesRef.current.setData(histData);
  }, [data]);

  return (
    <div className="relative rounded-lg bg-slate-900 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-300">Z-Score</h3>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded bg-red-500" />
            &gt;2σ
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded bg-green-500" />
            &lt;-2σ
          </span>
        </div>
      </div>
      <div ref={containerRef} className="w-full" />
    </div>
  );
}

export const ZScoreChart = memo(ZScoreChartComponent);
