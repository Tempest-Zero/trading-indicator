"""
Quant Engine - Main Integration Module

Combines all analysis components into a unified market analysis engine:
- Hurst Exponent for regime detection
- Kalman Filter for noise reduction
- Z-Score for statistical triggers
- Volume analysis for confirmation

Outputs a comprehensive MarketConditions dataclass with actionable insights.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from quant_engine.core.hurst import rolling_hurst, classify_regime, hurst_exponent
from quant_engine.core.kalman import kalman_smooth, adaptive_kalman
from quant_engine.core.zscore import rolling_zscore, multi_timeframe_zscore, classify_zscore_condition
from quant_engine.core.volume import volume_delta, volume_profile, relative_volume


@dataclass
class MarketConditions:
    """
    Output structure for comprehensive market analysis.

    Contains all analysis results and actionable insights.
    """
    # Identification
    symbol: str
    timestamp: str

    # Regime Analysis (Hurst Exponent)
    regime: str                      # TRENDING, MEAN_REVERTING, RANDOM_WALK
    regime_confidence: float         # 0-1 confidence in regime classification
    hurst_value: float               # Raw Hurst exponent value
    regime_description: str          # Human-readable description

    # Trend Analysis (Kalman Filter)
    current_price: float             # Current close price
    kalman_price: float              # Kalman-filtered price
    kalman_velocity: float           # Price velocity (trend direction/strength)
    kalman_acceleration: float       # Rate of velocity change
    trend_direction: str             # UP, DOWN, NEUTRAL
    price_vs_kalman: float           # Current price vs filtered price

    # Statistical Position (Z-Score)
    zscore: float                    # Current Z-Score
    percentile: float                # Current percentile (0-100)
    statistical_condition: str       # OVERSOLD, NEUTRAL, OVERBOUGHT, etc.
    zscore_mean: float               # Rolling mean
    zscore_std: float                # Rolling standard deviation

    # Volume Analysis
    volume_delta_pct: float          # Buy/sell pressure as percentage
    cumulative_delta_trend: str      # BULLISH, BEARISH
    relative_volume: float           # Current volume vs average
    buying_pressure: bool            # True if buying dominates
    selling_pressure: bool           # True if selling dominates

    # Key Levels (Volume Profile)
    poc: float                       # Point of Control
    value_area_high: float           # Upper value area bound
    value_area_low: float            # Lower value area bound

    # Probabilities and Insights
    pullback_probability: float      # Probability of pullback/reversal
    trend_continuation_probability: float  # Probability trend continues
    suggested_bias: str              # UP, DOWN, NEUTRAL, WAIT
    confidence: float                # Overall confidence (0-1)
    notes: List[str] = field(default_factory=list)  # Analysis notes

    def __str__(self) -> str:
        """Pretty print market conditions."""
        return f"""
{'='*60}
  MARKET ANALYSIS: {self.symbol}
  {self.timestamp}
{'='*60}

REGIME: {self.regime} (H={self.hurst_value:.3f})
   Confidence: {self.regime_confidence:.0%}
   {self.regime_description}

TREND: {self.trend_direction}
   Current Price: {self.current_price:.2f}
   Kalman Price:  {self.kalman_price:.2f}
   Velocity:      {self.kalman_velocity:.4f}

STATISTICAL POSITION: {self.statistical_condition}
   Z-Score:    {self.zscore:.2f}
   Percentile: {self.percentile:.0f}%

VOLUME:
   Delta %:          {self.volume_delta_pct:.1f}%
   Cumulative Trend: {self.cumulative_delta_trend}
   Relative Volume:  {self.relative_volume:.2f}x

KEY LEVELS:
   POC:         {self.poc:.2f}
   Value Area:  {self.value_area_low:.2f} - {self.value_area_high:.2f}

PROBABILITIES:
   Pullback:     {self.pullback_probability:.0%}
   Continuation: {self.trend_continuation_probability:.0%}

SUGGESTED BIAS: {self.suggested_bias}
   Confidence: {self.confidence:.0%}

NOTES:
{''.join(f'   - {note}' + chr(10) for note in self.notes)}
{'='*60}
"""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'regime': self.regime,
            'regime_confidence': self.regime_confidence,
            'hurst_value': self.hurst_value,
            'regime_description': self.regime_description,
            'current_price': self.current_price,
            'kalman_price': self.kalman_price,
            'kalman_velocity': self.kalman_velocity,
            'kalman_acceleration': self.kalman_acceleration,
            'trend_direction': self.trend_direction,
            'price_vs_kalman': self.price_vs_kalman,
            'zscore': self.zscore,
            'percentile': self.percentile,
            'statistical_condition': self.statistical_condition,
            'zscore_mean': self.zscore_mean,
            'zscore_std': self.zscore_std,
            'volume_delta_pct': self.volume_delta_pct,
            'cumulative_delta_trend': self.cumulative_delta_trend,
            'relative_volume': self.relative_volume,
            'buying_pressure': self.buying_pressure,
            'selling_pressure': self.selling_pressure,
            'poc': self.poc,
            'value_area_high': self.value_area_high,
            'value_area_low': self.value_area_low,
            'pullback_probability': self.pullback_probability,
            'trend_continuation_probability': self.trend_continuation_probability,
            'suggested_bias': self.suggested_bias,
            'confidence': self.confidence,
            'notes': self.notes
        }


class QuantEngine:
    """
    Main analysis engine combining all indicators.

    Provides comprehensive market analysis by integrating:
    - Hurst Exponent for regime detection
    - Kalman Filter for trend analysis
    - Z-Score for statistical positioning
    - Volume analysis for confirmation
    """

    def __init__(self,
                 hurst_window: int = 100,
                 hurst_smooth: int = 20,
                 zscore_window: int = 20,
                 kalman_process_noise: float = 0.01,
                 kalman_observation_noise: float = 1.0,
                 velocity_threshold: float = 0.1,
                 trend_threshold: float = 0.6,
                 revert_threshold: float = 0.4):
        """
        Initialize the Quant Engine.

        Args:
            hurst_window: Window for Hurst calculation (default 100)
            hurst_smooth: EMA smoothing for Hurst output (default 20)
            zscore_window: Window for Z-Score calculation (default 20)
            kalman_process_noise: Kalman transition covariance (default 0.01)
            kalman_observation_noise: Kalman observation covariance (default 1.0)
            velocity_threshold: Threshold for trend direction (default 0.1)
            trend_threshold: Hurst threshold for trending regime (default 0.6)
            revert_threshold: Hurst threshold for mean-reverting regime (default 0.4)
        """
        self.hurst_window = hurst_window
        self.hurst_smooth = hurst_smooth
        self.zscore_window = zscore_window
        self.kalman_process_noise = kalman_process_noise
        self.kalman_observation_noise = kalman_observation_noise
        self.velocity_threshold = velocity_threshold
        self.trend_threshold = trend_threshold
        self.revert_threshold = revert_threshold

        # Cache for intermediate results
        self._cache = {}

    def analyze(self,
                ohlcv: pd.DataFrame,
                symbol: str = "UNKNOWN") -> MarketConditions:
        """
        Run full analysis on OHLCV data.

        Args:
            ohlcv: DataFrame with columns [open, high, low, close, volume]
            symbol: Symbol name for identification

        Returns:
            MarketConditions dataclass with comprehensive analysis
        """
        prices = ohlcv['close'].values
        current_price = prices[-1]

        # Validate data
        if len(prices) < self.hurst_window:
            raise ValueError(
                f"Insufficient data: need at least {self.hurst_window} bars, got {len(prices)}"
            )

        # 1. Regime Detection (Hurst Exponent)
        hurst_series = rolling_hurst(
            prices,
            window=self.hurst_window,
            smooth=self.hurst_smooth
        )
        current_hurst = hurst_series[-1]
        regime_info = classify_regime(
            current_hurst,
            trend_threshold=self.trend_threshold,
            revert_threshold=self.revert_threshold
        )

        # 2. Kalman Filter
        kalman_result = kalman_smooth(
            prices,
            transition_covariance=self.kalman_process_noise,
            observation_covariance=self.kalman_observation_noise
        )
        kalman_price = kalman_result['filtered_price'][-1]
        kalman_velocity = kalman_result['velocity'][-1]
        kalman_acceleration = kalman_result['acceleration'][-1]

        # Classify trend direction
        if kalman_velocity > self.velocity_threshold:
            trend_direction = "UP"
        elif kalman_velocity < -self.velocity_threshold:
            trend_direction = "DOWN"
        else:
            trend_direction = "NEUTRAL"

        # 3. Z-Score
        zscore_result = rolling_zscore(prices, window=self.zscore_window)
        current_zscore = zscore_result['zscore'][-1]
        current_percentile = zscore_result['percentile'][-1]
        zscore_mean = zscore_result['mean'][-1]
        zscore_std = zscore_result['std'][-1]

        stat_condition, _ = classify_zscore_condition(current_zscore)

        # 4. Volume Analysis
        vol_delta_result = volume_delta(ohlcv)
        vol_delta_pct = vol_delta_result['delta_pct'][-1]
        cum_delta = vol_delta_result['cumulative_delta']
        buying_pressure = bool(vol_delta_result['buying_pressure'][-1])
        selling_pressure = bool(vol_delta_result['selling_pressure'][-1])

        # Cumulative delta trend (compare to 20 bars ago)
        lookback = min(20, len(cum_delta) - 1)
        if cum_delta[-1] > cum_delta[-lookback - 1]:
            cum_delta_trend = "BULLISH"
        else:
            cum_delta_trend = "BEARISH"

        # Relative volume
        rvol_result = relative_volume(ohlcv, window=20)
        current_rvol = rvol_result['rvol'][-1]

        # 5. Volume Profile
        vol_profile = volume_profile(ohlcv)

        # 6. Calculate Probabilities
        pullback_prob, continuation_prob, bias, confidence, notes = self._calculate_probabilities(
            regime_info=regime_info,
            trend_direction=trend_direction,
            stat_condition=stat_condition,
            vol_delta_pct=vol_delta_pct,
            cum_delta_trend=cum_delta_trend,
            current_price=current_price,
            kalman_price=kalman_price,
            current_zscore=current_zscore
        )

        # Cache intermediate results for visualization
        self._cache = {
            'hurst_series': hurst_series,
            'kalman_result': kalman_result,
            'zscore_result': zscore_result,
            'volume_delta': vol_delta_result,
            'volume_profile': vol_profile,
            'relative_volume': rvol_result
        }

        # Get timestamp
        if isinstance(ohlcv.index[-1], (datetime, pd.Timestamp)):
            timestamp = str(ohlcv.index[-1])
        else:
            timestamp = datetime.now().isoformat()

        return MarketConditions(
            symbol=symbol,
            timestamp=timestamp,
            regime=regime_info['regime'],
            regime_confidence=regime_info['confidence'],
            hurst_value=current_hurst if not np.isnan(current_hurst) else 0.5,
            regime_description=regime_info['description'],
            current_price=current_price,
            kalman_price=kalman_price,
            kalman_velocity=kalman_velocity,
            kalman_acceleration=kalman_acceleration,
            trend_direction=trend_direction,
            price_vs_kalman=current_price - kalman_price,
            zscore=current_zscore if not np.isnan(current_zscore) else 0.0,
            percentile=current_percentile if not np.isnan(current_percentile) else 50.0,
            statistical_condition=stat_condition,
            zscore_mean=zscore_mean if not np.isnan(zscore_mean) else current_price,
            zscore_std=zscore_std if not np.isnan(zscore_std) else 0.0,
            volume_delta_pct=vol_delta_pct if not np.isnan(vol_delta_pct) else 0.0,
            cumulative_delta_trend=cum_delta_trend,
            relative_volume=current_rvol if not np.isnan(current_rvol) else 1.0,
            buying_pressure=buying_pressure,
            selling_pressure=selling_pressure,
            poc=vol_profile['poc'],
            value_area_high=vol_profile['value_area_high'],
            value_area_low=vol_profile['value_area_low'],
            pullback_probability=pullback_prob,
            trend_continuation_probability=continuation_prob,
            suggested_bias=bias,
            confidence=confidence,
            notes=notes
        )

    def _calculate_probabilities(self,
                                 regime_info: Dict,
                                 trend_direction: str,
                                 stat_condition: str,
                                 vol_delta_pct: float,
                                 cum_delta_trend: str,
                                 current_price: float,
                                 kalman_price: float,
                                 current_zscore: float) -> Tuple[float, float, str, float, List[str]]:
        """
        Combine all factors into actionable probabilities.

        Returns:
            Tuple of (pullback_prob, continuation_prob, bias, confidence, notes)
        """
        notes = []

        # Base probabilities (50/50)
        pullback_prob = 0.5
        continuation_prob = 0.5

        # 1. Regime adjustments
        if regime_info['regime'] == 'TRENDING':
            continuation_prob += 0.15
            pullback_prob -= 0.10
            notes.append(
                f"Trending regime (H={regime_info['confidence']:.0%}) favors momentum"
            )
        elif regime_info['regime'] == 'MEAN_REVERTING':
            pullback_prob += 0.20
            continuation_prob -= 0.15
            notes.append("Mean-reverting regime - expect price to revert to mean")
        else:
            notes.append("Random walk regime - no statistical edge, reduce risk")

        # 2. Statistical position adjustments
        if 'OVERSOLD' in stat_condition:
            if regime_info['regime'] == 'MEAN_REVERTING':
                pullback_prob += 0.15
                notes.append(
                    f"Oversold in mean-reverting regime - bounce likely (Z={current_zscore:.2f})"
                )
            else:
                notes.append(
                    f"Statistically oversold (Z={current_zscore:.2f}) - watch for bounce"
                )
        elif 'OVERBOUGHT' in stat_condition:
            if regime_info['regime'] == 'MEAN_REVERTING':
                pullback_prob += 0.15
                notes.append(
                    f"Overbought in mean-reverting regime - pullback likely (Z={current_zscore:.2f})"
                )
            else:
                notes.append(
                    f"Statistically overbought (Z={current_zscore:.2f}) - watch for pullback"
                )

        # 3. Kalman filter insights
        if current_price > kalman_price * 1.02:
            notes.append("Price extended above Kalman trend")
        elif current_price < kalman_price * 0.98:
            notes.append("Price extended below Kalman trend")

        # 4. Volume confirmation
        if cum_delta_trend == 'BULLISH' and trend_direction == 'UP':
            continuation_prob += 0.10
            notes.append("Volume delta confirms uptrend")
        elif cum_delta_trend == 'BEARISH' and trend_direction == 'DOWN':
            continuation_prob += 0.10
            notes.append("Volume delta confirms downtrend")
        elif cum_delta_trend != trend_direction.replace('NEUTRAL', ''):
            pullback_prob += 0.05
            notes.append("Volume diverging from price trend")

        # 5. Normalize probabilities
        total = pullback_prob + continuation_prob
        pullback_prob /= total
        continuation_prob /= total

        # 6. Determine bias
        if continuation_prob > 0.6 and regime_info['regime'] == 'TRENDING':
            bias = trend_direction if trend_direction != 'NEUTRAL' else 'WAIT'
        elif pullback_prob > 0.6 and regime_info['regime'] == 'MEAN_REVERTING':
            # Fade the move
            if trend_direction == 'UP':
                bias = 'DOWN'  # Expect pullback in uptrend
            elif trend_direction == 'DOWN':
                bias = 'UP'   # Expect bounce in downtrend
            else:
                bias = 'WAIT'
        else:
            bias = 'NEUTRAL'

        # 7. Overall confidence
        confidence = max(pullback_prob, continuation_prob) * regime_info['confidence']
        confidence = min(confidence, 0.95)  # Cap at 95%

        return pullback_prob, continuation_prob, bias, confidence, notes

    def get_cached_data(self) -> Dict:
        """
        Get cached intermediate results from last analysis.

        Returns:
            Dictionary with hurst_series, kalman_result, zscore_result, etc.
        """
        return self._cache

    def analyze_multiple(self,
                         data: Dict[str, pd.DataFrame]) -> Dict[str, MarketConditions]:
        """
        Analyze multiple symbols.

        Args:
            data: Dictionary mapping symbol to OHLCV DataFrame

        Returns:
            Dictionary mapping symbol to MarketConditions
        """
        results = {}
        for symbol, ohlcv in data.items():
            try:
                results[symbol] = self.analyze(ohlcv, symbol=symbol)
            except Exception as e:
                print(f"Warning: Failed to analyze {symbol}: {e}")
                results[symbol] = None
        return results

    def quick_scan(self, ohlcv: pd.DataFrame, symbol: str = "UNKNOWN") -> Dict:
        """
        Quick market scan returning only essential metrics.

        Args:
            ohlcv: OHLCV DataFrame
            symbol: Symbol name

        Returns:
            Dictionary with essential metrics
        """
        prices = ohlcv['close'].values

        # Quick Hurst
        hurst = hurst_exponent(prices[-min(100, len(prices)):])
        regime_info = classify_regime(hurst)

        # Quick Kalman
        kalman = kalman_smooth(prices[-min(50, len(prices)):])

        # Quick Z-Score
        zscore = rolling_zscore(prices[-min(30, len(prices)):], window=20)

        return {
            'symbol': symbol,
            'price': prices[-1],
            'regime': regime_info['regime'],
            'hurst': hurst,
            'trend': 'UP' if kalman['velocity'][-1] > 0 else 'DOWN',
            'velocity': kalman['velocity'][-1],
            'zscore': zscore['zscore'][-1],
            'recommendation': regime_info['strategy']
        }


def create_engine(preset: str = 'default') -> QuantEngine:
    """
    Factory function to create QuantEngine with presets.

    Args:
        preset: One of 'default', 'fast', 'smooth', 'aggressive'

    Returns:
        Configured QuantEngine instance
    """
    presets = {
        'default': {
            'hurst_window': 100,
            'hurst_smooth': 20,
            'zscore_window': 20,
            'kalman_process_noise': 0.01,
            'kalman_observation_noise': 1.0,
        },
        'fast': {
            'hurst_window': 50,
            'hurst_smooth': 10,
            'zscore_window': 10,
            'kalman_process_noise': 0.05,
            'kalman_observation_noise': 0.5,
        },
        'smooth': {
            'hurst_window': 150,
            'hurst_smooth': 30,
            'zscore_window': 30,
            'kalman_process_noise': 0.005,
            'kalman_observation_noise': 2.0,
        },
        'aggressive': {
            'hurst_window': 100,
            'hurst_smooth': 10,
            'zscore_window': 15,
            'kalman_process_noise': 0.02,
            'kalman_observation_noise': 0.7,
            'velocity_threshold': 0.05,
        },
    }

    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")

    return QuantEngine(**presets[preset])
