"""
Volume Analysis Module

Analyzes volume to estimate buying vs selling pressure and identify key price levels.

Volume Delta: Estimates buy/sell pressure using price action within candles
Volume Profile: Shows where most trading occurred (support/resistance levels)
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple


def volume_delta(ohlcv: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Estimate buying vs selling pressure using price action.

    Method: Use candle body position within range to estimate
    - Close near high = buying pressure
    - Close near low = selling pressure

    Args:
        ohlcv: DataFrame with columns [open, high, low, close, volume]

    Returns:
        Dictionary with:
        - buy_volume: Estimated buying volume
        - sell_volume: Estimated selling volume
        - delta: buy_volume - sell_volume
        - delta_pct: Delta as percentage of total volume
        - cumulative_delta: Cumulative sum of delta
        - buying_pressure: Boolean (buy_ratio > 0.6)
        - selling_pressure: Boolean (buy_ratio < 0.4)
    """
    high = ohlcv['high'].values
    low = ohlcv['low'].values
    close = ohlcv['close'].values
    volume = ohlcv['volume'].values

    # Calculate price range, avoid division by zero
    price_range = high - low
    price_range = np.where(price_range < 1e-10, 1e-10, price_range)

    # Buy ratio: how close to high (0 = at low, 1 = at high)
    buy_ratio = (close - low) / price_range

    # Estimated buy/sell volume
    buy_volume = volume * buy_ratio
    sell_volume = volume * (1 - buy_ratio)

    # Delta
    delta = buy_volume - sell_volume
    cumulative_delta = np.cumsum(delta)

    # Normalized delta (as % of total volume)
    delta_pct = np.where(volume > 0, delta / volume * 100, 0)

    return {
        'buy_volume': buy_volume,
        'sell_volume': sell_volume,
        'delta': delta,
        'delta_pct': delta_pct,
        'cumulative_delta': cumulative_delta,
        'buy_ratio': buy_ratio,
        'buying_pressure': buy_ratio > 0.6,
        'selling_pressure': buy_ratio < 0.4,
        'neutral_pressure': (buy_ratio >= 0.4) & (buy_ratio <= 0.6)
    }


def volume_profile(ohlcv: pd.DataFrame,
                   num_bins: int = 20,
                   value_area_pct: float = 0.70) -> Dict[str, any]:
    """
    Create volume profile showing where most volume traded.
    Useful for finding support/resistance levels.

    Args:
        ohlcv: DataFrame with OHLCV data
        num_bins: Number of price bins
        value_area_pct: Percentage for value area calculation (default 70%)

    Returns:
        Dictionary with:
        - bins: Price bin edges
        - volume_at_level: Volume at each price level
        - poc: Point of Control (price with most volume)
        - value_area_high: Upper bound of value area
        - value_area_low: Lower bound of value area
        - high_volume_nodes: Prices with significant volume
    """
    close = ohlcv['close'].values
    high = ohlcv['high'].values
    low = ohlcv['low'].values
    volume = ohlcv['volume'].values

    # Use typical price for better distribution
    typical_price = (high + low + close) / 3

    price_min, price_max = np.min(low), np.max(high)
    bins = np.linspace(price_min, price_max, num_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    # Aggregate volume at each price level
    volume_at_level = np.zeros(num_bins)

    for i in range(len(typical_price)):
        # Find which bin this price falls into
        bin_idx = np.searchsorted(bins[1:], typical_price[i])
        bin_idx = min(bin_idx, num_bins - 1)
        volume_at_level[bin_idx] += volume[i]

    # Point of Control (POC) - price level with most volume
    poc_idx = np.argmax(volume_at_level)
    poc_price = bin_centers[poc_idx]

    # Value Area (value_area_pct of volume centered on POC)
    total_vol = np.sum(volume_at_level)
    target_vol = total_vol * value_area_pct

    # Start from POC and expand outward
    va_bins = {poc_idx}
    current_vol = volume_at_level[poc_idx]

    left_idx = poc_idx - 1
    right_idx = poc_idx + 1

    while current_vol < target_vol and (left_idx >= 0 or right_idx < num_bins):
        left_vol = volume_at_level[left_idx] if left_idx >= 0 else 0
        right_vol = volume_at_level[right_idx] if right_idx < num_bins else 0

        if left_vol >= right_vol and left_idx >= 0:
            va_bins.add(left_idx)
            current_vol += left_vol
            left_idx -= 1
        elif right_idx < num_bins:
            va_bins.add(right_idx)
            current_vol += right_vol
            right_idx += 1
        else:
            break

    va_low = bins[min(va_bins)]
    va_high = bins[max(va_bins) + 1]

    # High Volume Nodes (bins with volume > mean + 1 std)
    vol_mean = np.mean(volume_at_level)
    vol_std = np.std(volume_at_level)
    hvn_threshold = vol_mean + vol_std
    hvn_indices = np.where(volume_at_level > hvn_threshold)[0]
    high_volume_nodes = bin_centers[hvn_indices] if len(hvn_indices) > 0 else np.array([poc_price])

    # Low Volume Nodes (potential breakout zones)
    lvn_threshold = vol_mean - 0.5 * vol_std
    lvn_indices = np.where(volume_at_level < lvn_threshold)[0]
    low_volume_nodes = bin_centers[lvn_indices] if len(lvn_indices) > 0 else np.array([])

    return {
        'bins': bins,
        'bin_centers': bin_centers,
        'volume_at_level': volume_at_level,
        'poc': poc_price,
        'value_area_high': va_high,
        'value_area_low': va_low,
        'high_volume_nodes': high_volume_nodes,
        'low_volume_nodes': low_volume_nodes,
        'total_volume': total_vol
    }


def relative_volume(ohlcv: pd.DataFrame,
                    window: int = 20) -> Dict[str, np.ndarray]:
    """
    Calculate relative volume compared to historical average.

    RVOL > 1: Higher than average volume (potential significance)
    RVOL < 1: Lower than average volume

    Args:
        ohlcv: DataFrame with OHLCV data
        window: Lookback window for average

    Returns:
        Dictionary with relative volume metrics
    """
    volume = pd.Series(ohlcv['volume'].values)

    avg_volume = volume.rolling(window=window).mean()
    std_volume = volume.rolling(window=window).std()

    # Relative volume
    rvol = volume / avg_volume

    # Volume Z-Score
    vol_zscore = (volume - avg_volume) / std_volume

    return {
        'rvol': rvol.values,
        'avg_volume': avg_volume.values,
        'vol_zscore': vol_zscore.values,
        'high_volume': rvol.values > 1.5,
        'low_volume': rvol.values < 0.5,
        'extreme_volume': rvol.values > 2.0
    }


def volume_weighted_price(ohlcv: pd.DataFrame,
                          window: int = 20) -> Dict[str, np.ndarray]:
    """
    Calculate Volume Weighted Average Price (VWAP) and related metrics.

    Args:
        ohlcv: DataFrame with OHLCV data
        window: Rolling window for anchored VWAP

    Returns:
        Dictionary with VWAP and bands
    """
    high = ohlcv['high'].values
    low = ohlcv['low'].values
    close = ohlcv['close'].values
    volume = ohlcv['volume'].values

    # Typical price
    typical_price = (high + low + close) / 3

    # Session VWAP (cumulative)
    cum_vol = np.cumsum(volume)
    cum_tp_vol = np.cumsum(typical_price * volume)
    vwap = np.where(cum_vol > 0, cum_tp_vol / cum_vol, typical_price)

    # Rolling VWAP
    tp_series = pd.Series(typical_price * volume)
    vol_series = pd.Series(volume)

    rolling_tp_vol = tp_series.rolling(window=window).sum()
    rolling_vol = vol_series.rolling(window=window).sum()
    rolling_vwap = (rolling_tp_vol / rolling_vol).values

    # VWAP bands (standard deviation based)
    squared_diff = (typical_price - vwap) ** 2 * volume
    cum_sq_diff = np.cumsum(squared_diff)
    variance = np.where(cum_vol > 0, cum_sq_diff / cum_vol, 0)
    vwap_std = np.sqrt(variance)

    return {
        'vwap': vwap,
        'rolling_vwap': rolling_vwap,
        'upper_band_1': vwap + vwap_std,
        'lower_band_1': vwap - vwap_std,
        'upper_band_2': vwap + 2 * vwap_std,
        'lower_band_2': vwap - 2 * vwap_std,
        'price_vs_vwap': close - vwap,
        'above_vwap': close > vwap
    }


def on_balance_volume(ohlcv: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Calculate On-Balance Volume (OBV) and its momentum.

    OBV accumulates volume based on price direction:
    - Price up: Add volume
    - Price down: Subtract volume

    Args:
        ohlcv: DataFrame with OHLCV data

    Returns:
        Dictionary with OBV and related metrics
    """
    close = ohlcv['close'].values
    volume = ohlcv['volume'].values

    # Calculate price direction
    price_change = np.diff(close, prepend=close[0])

    # OBV calculation
    obv_direction = np.sign(price_change)
    obv_direction[price_change == 0] = 0

    obv = np.cumsum(volume * obv_direction)

    # OBV momentum (rate of change)
    obv_series = pd.Series(obv)
    obv_ema = obv_series.ewm(span=20).mean().values
    obv_momentum = obv - obv_ema

    # OBV trend
    obv_sma_20 = obv_series.rolling(20).mean().values
    obv_sma_50 = obv_series.rolling(50).mean().values

    return {
        'obv': obv,
        'obv_ema': obv_ema,
        'obv_momentum': obv_momentum,
        'obv_trend': np.sign(obv_sma_20 - obv_sma_50),
        'obv_divergence': np.sign(price_change) != np.sign(np.diff(obv, prepend=obv[0]))
    }


def volume_momentum(ohlcv: pd.DataFrame,
                    short_window: int = 5,
                    long_window: int = 20) -> Dict[str, np.ndarray]:
    """
    Calculate volume momentum indicators.

    Args:
        ohlcv: DataFrame with OHLCV data
        short_window: Short-term average window
        long_window: Long-term average window

    Returns:
        Dictionary with volume momentum metrics
    """
    volume = pd.Series(ohlcv['volume'].values)
    close = ohlcv['close'].values

    # Volume moving averages
    vol_sma_short = volume.rolling(short_window).mean()
    vol_sma_long = volume.rolling(long_window).mean()

    # Volume ratio (short vs long)
    vol_ratio = vol_sma_short / vol_sma_long

    # Volume trend
    vol_trend = np.sign(vol_sma_short.values - vol_sma_long.values)

    # Price-Volume correlation
    price_series = pd.Series(close)
    pv_corr = price_series.rolling(long_window).corr(volume)

    # Force Index (price change * volume)
    price_change = np.diff(close, prepend=close[0])
    force = price_change * volume.values

    force_series = pd.Series(force)
    force_ema = force_series.ewm(span=short_window).mean()

    return {
        'vol_ratio': vol_ratio.values,
        'vol_trend': vol_trend,
        'pv_correlation': pv_corr.values,
        'force_index': force,
        'force_ema': force_ema.values,
        'volume_expanding': vol_ratio.values > 1.2,
        'volume_contracting': vol_ratio.values < 0.8
    }


def accumulation_distribution(ohlcv: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Calculate Accumulation/Distribution Line.

    The A/D line uses the close location value (CLV) to weight volume:
    - CLV = [(Close - Low) - (High - Close)] / (High - Low)
    - A/D = Previous A/D + CLV * Volume

    Args:
        ohlcv: DataFrame with OHLCV data

    Returns:
        Dictionary with A/D line and related metrics
    """
    high = ohlcv['high'].values
    low = ohlcv['low'].values
    close = ohlcv['close'].values
    volume = ohlcv['volume'].values

    # Money Flow Multiplier (CLV)
    price_range = high - low
    price_range = np.where(price_range < 1e-10, 1e-10, price_range)

    clv = ((close - low) - (high - close)) / price_range

    # Money Flow Volume
    mf_volume = clv * volume

    # A/D Line
    ad_line = np.cumsum(mf_volume)

    # A/D Line EMA for trend
    ad_series = pd.Series(ad_line)
    ad_ema = ad_series.ewm(span=20).mean().values

    return {
        'ad_line': ad_line,
        'ad_ema': ad_ema,
        'clv': clv,
        'mf_volume': mf_volume,
        'ad_trend': np.sign(ad_line - ad_ema),
        'accumulation': clv > 0.3,
        'distribution': clv < -0.3
    }


def volume_analysis_summary(ohlcv: pd.DataFrame) -> Dict[str, any]:
    """
    Generate comprehensive volume analysis summary.

    Args:
        ohlcv: DataFrame with OHLCV data

    Returns:
        Dictionary with all volume analysis metrics
    """
    delta = volume_delta(ohlcv)
    profile = volume_profile(ohlcv)
    rvol = relative_volume(ohlcv)
    vwap = volume_weighted_price(ohlcv)
    obv = on_balance_volume(ohlcv)
    momentum = volume_momentum(ohlcv)
    ad = accumulation_distribution(ohlcv)

    # Current values (latest bar)
    current = {
        'delta_pct': delta['delta_pct'][-1],
        'cumulative_delta': delta['cumulative_delta'][-1],
        'rvol': rvol['rvol'][-1],
        'price_vs_vwap': vwap['price_vs_vwap'][-1],
        'obv_trend': obv['obv_trend'][-1],
        'vol_trend': momentum['vol_trend'][-1],
        'ad_trend': ad['ad_trend'][-1],
        'poc': profile['poc'],
        'value_area_high': profile['value_area_high'],
        'value_area_low': profile['value_area_low']
    }

    # Bias determination
    buy_signals = sum([
        delta['buying_pressure'][-1],
        vwap['above_vwap'][-1],
        obv['obv_trend'][-1] > 0,
        ad['accumulation'][-1]
    ])

    sell_signals = sum([
        delta['selling_pressure'][-1],
        not vwap['above_vwap'][-1],
        obv['obv_trend'][-1] < 0,
        ad['distribution'][-1]
    ])

    if buy_signals >= 3:
        current['volume_bias'] = 'BULLISH'
    elif sell_signals >= 3:
        current['volume_bias'] = 'BEARISH'
    else:
        current['volume_bias'] = 'NEUTRAL'

    current['buy_signal_count'] = int(buy_signals)
    current['sell_signal_count'] = int(sell_signals)

    return {
        'delta': delta,
        'profile': profile,
        'relative_volume': rvol,
        'vwap': vwap,
        'obv': obv,
        'momentum': momentum,
        'accumulation_distribution': ad,
        'current': current
    }
