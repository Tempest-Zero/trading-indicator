'use client';

import { useEffect, useRef, memo } from 'react';
import { createChart, IChartApi, ISeriesApi, HistogramData, ColorType } from 'lightweight-charts';
import type { ChartData } from '@/types';

interface VolumeChartProps {
  data: ChartData | undefined;
  height?: number;
}

function VolumeChartComponent({ data, height = 120 }: VolumeChartProps) {
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

    // Histogram series for volume delta
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

    // Format volume delta data
    const volumeData: HistogramData[] = data.ohlcv.map((bar, i) => {
      const delta = data.volume_delta[i] ?? 0;
      return {
        time: bar.timestamp.split('T')[0] as string,
        value: delta,
        color: delta >= 0 ? '#22c55e' : '#ef4444',
      };
    });

    seriesRef.current.setData(volumeData);
  }, [data]);

  return (
    <div className="relative rounded-lg bg-slate-900 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-300">Volume Delta</h3>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded bg-green-500" />
            Buy
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded bg-red-500" />
            Sell
          </span>
        </div>
      </div>
      <div ref={containerRef} className="w-full" />
    </div>
  );
}

export const VolumeChart = memo(VolumeChartComponent);
