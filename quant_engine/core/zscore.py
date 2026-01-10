"""
Z-Score Engine Module

Calculates Z-Score of price relative to rolling statistics.
Z-Score measures how many standard deviations away from the mean a value is.

Z = (price - mean) / std

Key thresholds:
- Z > 2: Statistically overbought (95th percentile)
- Z < -2: Statistically oversold (5th percentile)
- |Z| > 3: Extreme (99th percentile)

Unlike fixed RSI thresholds, Z-Score adapts to current volatility.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


def rolling_zscore(prices: np.ndarray,
                   window: int = 20,
                   min_periods: Optional[int] = None) -> Dict[str, np.ndarray]:
    """
    Calculate Z-Score of price relative to rolling statistics.

    Z = (price - rolling_mean) / rolling_std

    Args:
        prices: Price array
        window: Rolling window for mean and std calculation
        min_periods: Minimum periods required (default: window)

    Returns:
        Dictionary with:
        - zscore: Current standardized deviation
        - mean: Rolling mean
        - std: Rolling standard deviation
        - percentile: Where current price sits in distribution (0-100)
        - extreme_low: Boolean array (Z < -2)
        - extreme_high: Boolean array (Z > 2)
        - mild_low: Boolean array (-2 <= Z < -1)
        - mild_high: Boolean array (1 < Z <= 2)
    """
    if min_periods is None:
        min_periods = window

    series = pd.Series(prices)

    rolling_mean = series.rolling(window=window, min_periods=min_periods).mean()
    rolling_std = series.rolling(window=window, min_periods=min_periods).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0, np.nan)

    zscore = (series - rolling_mean) / rolling_std

    # Calculate percentile (what % of rolling window is below current price)
    def calc_percentile(window_data):
        if len(window_data) < 2 or np.isnan(window_data).any():
            return 50.0
        current = window_data.iloc[-1]
        historical = window_data.iloc[:-1]
        return (historical < current).sum() / len(historical) * 100

    percentile = series.rolling(window=window, min_periods=min_periods).apply(
        calc_percentile, raw=False
    )

    zscore_arr = zscore.values
    percentile_arr = percentile.values

    return {
        'zscore': zscore_arr,
        'mean': rolling_mean.values,
        'std': rolling_std.values,
        'percentile': percentile_arr,
        'extreme_low': zscore_arr < -2,
        'extreme_high': zscore_arr > 2,
        'mild_low': (zscore_arr >= -2) & (zscore_arr < -1),
        'mild_high': (zscore_arr > 1) & (zscore_arr <= 2),
        'neutral': (zscore_arr >= -1) & (zscore_arr <= 1)
    }


def multi_timeframe_zscore(prices: np.ndarray,
                           windows: List[int] = [20, 50, 100]) -> Dict[str, np.ndarray]:
    """
    Calculate Z-Scores across multiple timeframes for confluence analysis.

    When all timeframes agree (all oversold or all overbought), the signal
    is more reliable.

    Args:
        prices: Price array
        windows: List of window sizes to use

    Returns:
        Dictionary with:
        - z_{window}: Z-score for each window
        - confluence: Average of signs (-1 to 1)
        - aligned_oversold: All timeframes agree oversold
        - aligned_overbought: All timeframes agree overbought
        - strength: Confluence strength (0-1)
    """
    results = {}

    for w in windows:
        z_result = rolling_zscore(prices, window=w)
        results[f'z_{w}'] = z_result['zscore']

    # Calculate confluence (average of signs across timeframes)
    z_arrays = np.array([results[f'z_{w}'] for w in windows])

    # Handle NaN values
    signs = np.sign(z_arrays)
    with np.errstate(all='ignore'):
        confluence = np.nanmean(signs, axis=0)

    # Strong agreement when average is close to -1 or +1
    results['confluence'] = confluence
    results['aligned_oversold'] = confluence < -0.8
    results['aligned_overbought'] = confluence > 0.8
    results['strength'] = np.abs(confluence)

    # Calculate average absolute zscore for signal strength
    with np.errstate(all='ignore'):
        avg_abs_z = np.nanmean(np.abs(z_arrays), axis=0)
    results['avg_magnitude'] = avg_abs_z

    return results


def zscore_bands(prices: np.ndarray,
                 window: int = 20,
                 num_bands: int = 3) -> Dict[str, np.ndarray]:
    """
    Calculate Z-Score based price bands (similar to Bollinger Bands).

    Returns bands at each standard deviation level.

    Args:
        prices: Price array
        window: Rolling window
        num_bands: Number of bands (1 = ±1σ, 2 = ±2σ, etc.)

    Returns:
        Dictionary with mean and upper/lower bands for each σ level
    """
    series = pd.Series(prices)
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()

    result = {
        'mean': rolling_mean.values,
        'std': rolling_std.values,
        'price': prices
    }

    for i in range(1, num_bands + 1):
        result[f'upper_{i}'] = (rolling_mean + i * rolling_std).values
        result[f'lower_{i}'] = (rolling_mean - i * rolling_std).values

    return result


def zscore_mean_reversion_signal(prices: np.ndarray,
                                 window: int = 20,
                                 entry_threshold: float = 2.0,
                                 exit_threshold: float = 0.5) -> Dict[str, np.ndarray]:
    """
    Generate mean reversion signals based on Z-Score.

    Signal logic:
    - Long when Z < -entry_threshold (oversold)
    - Short when Z > entry_threshold (overbought)
    - Exit when |Z| < exit_threshold

    Args:
        prices: Price array
        window: Rolling window
        entry_threshold: Z-Score threshold for entry (default 2.0)
        exit_threshold: Z-Score threshold for exit (default 0.5)

    Returns:
        Dictionary with:
        - signal: +1 (long), -1 (short), 0 (neutral/exit)
        - zscore: Current Z-Score
        - entry_long: Entry signal for long
        - entry_short: Entry signal for short
        - exit: Exit signal
    """
    z_result = rolling_zscore(prices, window=window)
    zscore = z_result['zscore']

    n = len(prices)
    signal = np.zeros(n)
    position = 0

    entry_long = np.zeros(n, dtype=bool)
    entry_short = np.zeros(n, dtype=bool)
    exit_signal = np.zeros(n, dtype=bool)

    for i in range(window, n):
        z = zscore[i]

        if np.isnan(z):
            signal[i] = position
            continue

        # Entry signals
        if position == 0:
            if z < -entry_threshold:
                position = 1
                entry_long[i] = True
            elif z > entry_threshold:
                position = -1
                entry_short[i] = True

        # Exit signals
        elif position != 0:
            if abs(z) < exit_threshold:
                exit_signal[i] = True
                position = 0

        signal[i] = position

    return {
        'signal': signal,
        'zscore': zscore,
        'entry_long': entry_long,
        'entry_short': entry_short,
        'exit': exit_signal,
        'mean': z_result['mean'],
        'std': z_result['std']
    }


def dynamic_zscore_threshold(prices: np.ndarray,
                             window: int = 20,
                             vol_window: int = 50,
                             base_threshold: float = 2.0) -> Dict[str, np.ndarray]:
    """
    Calculate dynamic Z-Score thresholds based on volatility regime.

    In high volatility regimes, use wider thresholds.
    In low volatility regimes, use tighter thresholds.

    Args:
        prices: Price array
        window: Z-Score window
        vol_window: Volatility regime window
        base_threshold: Base threshold (adjusted by regime)

    Returns:
        Dictionary with zscore and dynamic thresholds
    """
    z_result = rolling_zscore(prices, window=window)
    zscore = z_result['zscore']

    # Calculate volatility regime
    series = pd.Series(prices)
    returns = series.pct_change()
    volatility = returns.rolling(vol_window).std()

    # Normalize volatility to [0.5, 1.5] range
    vol_min = volatility.rolling(vol_window).min()
    vol_max = volatility.rolling(vol_window).max()

    with np.errstate(all='ignore'):
        vol_percentile = (volatility - vol_min) / (vol_max - vol_min + 1e-10)

    # Dynamic threshold: higher vol = higher threshold
    threshold_multiplier = 0.5 + vol_percentile.values  # Range: [0.5, 1.5]
    dynamic_upper = base_threshold * threshold_multiplier
    dynamic_lower = -base_threshold * threshold_multiplier

    return {
        'zscore': zscore,
        'upper_threshold': dynamic_upper,
        'lower_threshold': dynamic_lower,
        'vol_regime': vol_percentile.values,
        'extreme_high': zscore > dynamic_upper,
        'extreme_low': zscore < dynamic_lower
    }


def zscore_divergence(prices: np.ndarray,
                      indicator: np.ndarray,
                      window: int = 20,
                      lookback: int = 10) -> Dict[str, np.ndarray]:
    """
    Detect divergence between price Z-Score and another indicator.

    Bullish divergence: Price makes lower low but indicator makes higher low
    Bearish divergence: Price makes higher high but indicator makes lower high

    Args:
        prices: Price array
        indicator: Secondary indicator array (e.g., RSI, volume)
        window: Z-Score window
        lookback: Lookback for divergence detection

    Returns:
        Dictionary with divergence signals
    """
    price_z = rolling_zscore(prices, window=window)['zscore']
    ind_z = rolling_zscore(indicator, window=window)['zscore']

    n = len(prices)
    bullish_div = np.zeros(n, dtype=bool)
    bearish_div = np.zeros(n, dtype=bool)

    for i in range(lookback + window, n):
        # Get recent lows and highs
        price_window = prices[i - lookback:i + 1]
        ind_window = indicator[i - lookback:i + 1]

        # Current is at local low
        if prices[i] == np.min(price_window):
            # Find previous local low
            prev_low_idx = np.argmin(price_window[:-1])
            prev_low_price = price_window[prev_low_idx]
            prev_low_ind = ind_window[prev_low_idx]

            # Bullish: price lower low, indicator higher low
            if prices[i] < prev_low_price and indicator[i] > prev_low_ind:
                bullish_div[i] = True

        # Current is at local high
        if prices[i] == np.max(price_window):
            # Find previous local high
            prev_high_idx = np.argmax(price_window[:-1])
            prev_high_price = price_window[prev_high_idx]
            prev_high_ind = ind_window[prev_high_idx]

            # Bearish: price higher high, indicator lower high
            if prices[i] > prev_high_price and indicator[i] < prev_high_ind:
                bearish_div[i] = True

    return {
        'price_zscore': price_z,
        'indicator_zscore': ind_z,
        'bullish_divergence': bullish_div,
        'bearish_divergence': bearish_div
    }


def classify_zscore_condition(zscore: float) -> Tuple[str, float]:
    """
    Classify the current Z-Score condition.

    Args:
        zscore: Current Z-Score value

    Returns:
        Tuple of (condition_name, extremity_score)
    """
    if np.isnan(zscore):
        return ('UNKNOWN', 0.0)

    abs_z = abs(zscore)

    if abs_z < 0.5:
        return ('NEUTRAL', 0.0)
    elif abs_z < 1.0:
        if zscore > 0:
            return ('SLIGHTLY_HIGH', abs_z)
        else:
            return ('SLIGHTLY_LOW', abs_z)
    elif abs_z < 2.0:
        if zscore > 0:
            return ('HIGH', abs_z)
        else:
            return ('LOW', abs_z)
    elif abs_z < 3.0:
        if zscore > 0:
            return ('OVERBOUGHT', abs_z)
        else:
            return ('OVERSOLD', abs_z)
    else:
        if zscore > 0:
            return ('EXTREME_OVERBOUGHT', min(abs_z, 5.0))
        else:
            return ('EXTREME_OVERSOLD', min(abs_z, 5.0))
