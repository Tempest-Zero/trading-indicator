'use client';

import { useEffect, useRef, memo } from 'react';
import { createChart, IChartApi, ISeriesApi, LineData, ColorType } from 'lightweight-charts';
import type { ChartData } from '@/types';

interface HurstChartProps {
  data: ChartData | undefined;
  height?: number;
}

function HurstChartComponent({ data, height = 120 }: HurstChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);

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

    // Line series for Hurst exponent
    const series = chart.addLineSeries({
      color: '#8b5cf6',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    });

    // Add 0.5 reference line
    chart.addLineSeries({
      color: '#475569',
      lineWidth: 1,
      lineStyle: 2,
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

    // Format Hurst data
    const hurstData: LineData[] = data.ohlcv.map((bar, i) => ({
      time: bar.timestamp.split('T')[0] as string,
      value: data.hurst_series[i] ?? 0.5,
    }));

    seriesRef.current.setData(hurstData);
  }, [data]);

  return (
    <div className="relative rounded-lg bg-slate-900 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-300">Hurst Exponent</h3>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>&gt;0.5 Trending</span>
          <span>&lt;0.5 Mean Revert</span>
        </div>
      </div>
      <div ref={containerRef} className="w-full" />
    </div>
  );
}

export const HurstChart = memo(HurstChartComponent);
