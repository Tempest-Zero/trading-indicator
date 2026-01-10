"""
Hurst Exponent Module

Calculates the Hurst Exponent for market regime detection.
The Hurst Exponent (H) indicates the tendency of a time series:
- H < 0.5: Mean-reverting (choppy market)
- H ≈ 0.5: Random walk (no statistical edge)
- H > 0.5: Trending (momentum works)

Uses the Rescaled Range (R/S) method, which is most robust for financial data.
"""

import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple


def hurst_exponent(prices: np.ndarray, max_lag: int = 100) -> float:
    """
    Calculate Hurst Exponent using R/S (Rescaled Range) method.

    The R/S method:
    1. Calculate returns for varying lag sizes
    2. For each lag, compute cumulative deviation from mean
    3. Calculate R = range of cumulative deviation
    4. Calculate S = standard deviation of returns
    5. R/S scales as lag^H, so log(R/S) vs log(lag) gives H

    Args:
        prices: Price array (at least max_lag + 10 elements recommended)
        max_lag: Maximum lag for R/S calculation (default 100)

    Returns:
        Hurst exponent H:
        - H < 0.5: Mean-reverting (antipersistent)
        - H ≈ 0.5: Random walk (Brownian motion)
        - H > 0.5: Trending (persistent)
    """
    if len(prices) < 20:
        return 0.5  # Insufficient data

    # Ensure we have enough data points
    max_lag = min(max_lag, len(prices) - 10)

    lags = range(10, max_lag)
    rs_values = []
    valid_lags = []

    for lag in lags:
        # Calculate returns for this window
        returns = np.diff(prices[:lag + 1])

        if len(returns) < 2:
            continue

        # Mean-adjust the returns
        mean_return = np.mean(returns)
        adjusted = returns - mean_return

        # Cumulative deviation from mean
        cumdev = np.cumsum(adjusted)

        # Range of cumulative deviation
        R = np.max(cumdev) - np.min(cumdev)

        # Standard deviation of returns
        S = np.std(returns, ddof=1)

        if S > 1e-10 and R > 1e-10:
            rs_values.append(R / S)
            valid_lags.append(lag)

    if len(rs_values) < 10:
        return 0.5  # Insufficient data for reliable estimate

    # Log-log regression to find H
    log_lags = np.log(np.array(valid_lags))
    log_rs = np.log(np.array(rs_values))

    # Linear regression: log(R/S) = H * log(lag) + c
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_lags, log_rs)

    # Clamp to valid range [0, 1]
    return np.clip(slope, 0.0, 1.0)


def hurst_exponent_dfa(prices: np.ndarray, min_scale: int = 10, max_scale: int = 100) -> float:
    """
    Calculate Hurst Exponent using Detrended Fluctuation Analysis (DFA).

    DFA is more robust to non-stationarities than R/S analysis.
    It's particularly useful for financial time series.

    Args:
        prices: Price array
        min_scale: Minimum window scale
        max_scale: Maximum window scale

    Returns:
        Hurst exponent H
    """
    if len(prices) < max_scale:
        return 0.5

    # Convert to log returns and cumulative sum
    returns = np.diff(np.log(prices + 1e-10))
    cumsum = np.cumsum(returns - np.mean(returns))

    # Scales to analyze
    scales = np.logspace(np.log10(min_scale), np.log10(max_scale), 20).astype(int)
    scales = np.unique(scales[scales >= min_scale])

    fluctuations = []
    valid_scales = []

    for scale in scales:
        if scale > len(cumsum) // 4:
            continue

        # Split into non-overlapping segments
        n_segments = len(cumsum) // scale
        if n_segments < 1:
            continue

        f2 = []
        for seg in range(n_segments):
            start = seg * scale
            end = start + scale
            segment = cumsum[start:end]

            # Detrend with linear fit
            x = np.arange(scale)
            coeffs = np.polyfit(x, segment, 1)
            trend = np.polyval(coeffs, x)

            # Fluctuation
            f2.append(np.mean((segment - trend) ** 2))

        if f2:
            fluctuations.append(np.sqrt(np.mean(f2)))
            valid_scales.append(scale)

    if len(fluctuations) < 5:
        return 0.5

    # Log-log regression
    log_scales = np.log(np.array(valid_scales))
    log_fluct = np.log(np.array(fluctuations))

    slope, _, _, _, _ = stats.linregress(log_scales, log_fluct)

    return np.clip(slope, 0.0, 1.0)


def rolling_hurst(prices: np.ndarray,
                  window: int = 100,
                  smooth: int = 20,
                  method: str = 'rs') -> np.ndarray:
    """
    Calculate rolling Hurst Exponent with EMA smoothing.

    Computes Hurst exponent for each rolling window, then applies
    EMA smoothing to reduce noise in the output.

    Args:
        prices: Price array
        window: Lookback window for each Hurst calculation
        smooth: EMA smoothing period for output
        method: 'rs' for R/S method, 'dfa' for DFA method

    Returns:
        Array of smoothed Hurst values (NaN for first 'window' elements)
    """
    n = len(prices)
    hurst_values = np.full(n, np.nan)

    # Select calculation method
    calc_func = hurst_exponent if method == 'rs' else hurst_exponent_dfa

    # Calculate rolling Hurst
    for i in range(window, n):
        h = calc_func(prices[i - window:i])
        hurst_values[i] = h

    # Apply EMA smoothing
    if smooth > 1:
        alpha = 2 / (smooth + 1)
        smoothed = np.full(n, np.nan)

        # Find first valid value
        first_valid = window
        smoothed[first_valid] = hurst_values[first_valid]

        for i in range(first_valid + 1, n):
            if not np.isnan(hurst_values[i]):
                if np.isnan(smoothed[i - 1]):
                    smoothed[i] = hurst_values[i]
                else:
                    smoothed[i] = alpha * hurst_values[i] + (1 - alpha) * smoothed[i - 1]

        return smoothed

    return hurst_values


def classify_regime(hurst: float,
                    trend_threshold: float = 0.6,
                    revert_threshold: float = 0.4) -> Dict:
    """
    Classify market regime from Hurst value.

    Args:
        hurst: Current Hurst exponent value
        trend_threshold: H above this is considered trending (default 0.6)
        revert_threshold: H below this is considered mean-reverting (default 0.4)

    Returns:
        Dictionary with regime classification:
        - regime: 'MEAN_REVERTING', 'RANDOM_WALK', or 'TRENDING'
        - confidence: Confidence level (0-1)
        - strategy: Suggested strategy approach
        - description: Human-readable description
    """
    if np.isnan(hurst):
        return {
            'regime': 'UNKNOWN',
            'confidence': 0.0,
            'strategy': 'WAIT',
            'description': 'Insufficient data to determine regime'
        }

    if hurst < revert_threshold:
        # Mean-reverting regime
        confidence = min(1.0, (revert_threshold - hurst) / revert_threshold * 2)
        return {
            'regime': 'MEAN_REVERTING',
            'confidence': confidence,
            'strategy': 'FADE_EXTREMES',
            'description': 'Choppy market - buy dips, sell rips, fade extremes'
        }

    elif hurst > trend_threshold:
        # Trending regime
        confidence = min(1.0, (hurst - trend_threshold) / (1 - trend_threshold) * 2)
        return {
            'regime': 'TRENDING',
            'confidence': confidence,
            'strategy': 'FOLLOW_MOMENTUM',
            'description': 'Trending market - buy breakouts, hold winners, trail stops'
        }

    else:
        # Random walk (no edge)
        distance_from_center = abs(hurst - 0.5)
        confidence = 1 - distance_from_center * 4  # Higher confidence when H is exactly 0.5
        return {
            'regime': 'RANDOM_WALK',
            'confidence': max(0, confidence),
            'strategy': 'REDUCE_RISK',
            'description': 'No statistical edge - reduce position size, wait for clearer regime'
        }


def regime_strength(hurst: float) -> Tuple[str, float]:
    """
    Get regime strength as a simple tuple.

    Args:
        hurst: Hurst exponent value

    Returns:
        Tuple of (regime_name, strength) where strength is 0-1
    """
    if np.isnan(hurst):
        return ('UNKNOWN', 0.0)

    if hurst < 0.35:
        return ('STRONG_MEAN_REVERT', min(1.0, (0.35 - hurst) / 0.35))
    elif hurst < 0.45:
        return ('WEAK_MEAN_REVERT', (0.45 - hurst) / 0.1)
    elif hurst < 0.55:
        return ('RANDOM_WALK', 1 - abs(hurst - 0.5) * 10)
    elif hurst < 0.65:
        return ('WEAK_TREND', (hurst - 0.55) / 0.1)
    else:
        return ('STRONG_TREND', min(1.0, (hurst - 0.65) / 0.35))


def detect_regime_change(hurst_series: np.ndarray,
                         lookback: int = 20,
                         threshold: float = 0.1) -> np.ndarray:
    """
    Detect regime changes in the Hurst exponent series.

    A regime change is detected when:
    1. Hurst crosses from one zone to another (e.g., trending to mean-reverting)
    2. Hurst changes significantly within its lookback period

    Args:
        hurst_series: Array of Hurst values
        lookback: Lookback period for change detection
        threshold: Minimum change to trigger detection

    Returns:
        Array of regime change signals:
        -1 = shift toward mean-reversion
        0 = no change
        +1 = shift toward trending
    """
    n = len(hurst_series)
    changes = np.zeros(n)

    for i in range(lookback, n):
        if np.isnan(hurst_series[i]) or np.isnan(hurst_series[i - lookback]):
            continue

        delta = hurst_series[i] - hurst_series[i - lookback]

        if abs(delta) >= threshold:
            changes[i] = np.sign(delta)

    return changes
