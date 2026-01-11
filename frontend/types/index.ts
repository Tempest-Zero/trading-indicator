// ============ ANALYSIS TYPES ============

export interface RegimeData {
  regime: 'TRENDING' | 'MEAN_REVERTING' | 'RANDOM_WALK' | 'UNKNOWN';
  confidence: number;
  hurst_value: number;
  description: string;
}

export interface TrendData {
  direction: 'UP' | 'DOWN' | 'NEUTRAL';
  kalman_price: number;
  velocity: number;
}

export interface StatisticalData {
  zscore: number;
  percentile: number;
  condition: string;
}

export interface VolumeData {
  delta_pct: number;
  cumulative_trend: 'BULLISH' | 'BEARISH';
}

export interface KeyLevels {
  poc: number;
  value_area_high: number;
  value_area_low: number;
}

export interface FullAnalysis {
  symbol: string;
  timestamp: string;
  current_price: number;
  regime: RegimeData;
  trend: TrendData;
  statistical: StatisticalData;
  volume: VolumeData;
  key_levels: KeyLevels;
  pullback_probability: number;
  continuation_probability: number;
  suggested_bias: 'UP' | 'DOWN' | 'NEUTRAL' | 'WAIT';
  confidence: number;
  notes: string[];
}

// ============ CHART TYPES ============

export interface OHLCVBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartData {
  symbol: string;
  timeframe: string;
  ohlcv: OHLCVBar[];
  kalman_line: number[];
  hurst_series: number[];
  zscore_series: number[];
  volume_delta: number[];
}

// ============ UI TYPES ============

export type Timeframe = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

export interface TimeframeOption {
  value: Timeframe;
  label: string;
}

export interface SymbolCategory {
  crypto: string[];
  stocks: string[];
  indices: string[];
}

// ============ WEBSOCKET TYPES ============

export interface WSMessage {
  type: 'subscribed' | 'unsubscribed' | 'analysis' | 'error';
  data?: FullAnalysis;
  symbols?: string[];
  message?: string;
}
