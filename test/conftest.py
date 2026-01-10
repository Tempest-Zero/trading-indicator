"""
Pytest fixtures and test data generators for Quant Engine tests.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def synthetic_trending_data():
    """Generate synthetic data with known trending behavior (H > 0.5)"""
    np.random.seed(42)
    n = 500
    # Trending series: cumulative sum of biased random walk
    trend = np.cumsum(np.random.normal(0.1, 1, n))  # Positive drift
    noise = np.random.normal(0, 0.5, n)
    prices = 100 + trend + noise

    return _create_ohlcv(prices)


@pytest.fixture
def synthetic_mean_reverting_data():
    """Generate synthetic data with known mean-reverting behavior (H < 0.5)"""
    np.random.seed(42)
    n = 500
    # Ornstein-Uhlenbeck process (mean-reverting)
    theta = 0.7  # Mean reversion speed
    mu = 100     # Long-term mean
    sigma = 2    # Volatility

    prices = np.zeros(n)
    prices[0] = mu
    for i in range(1, n):
        prices[i] = prices[i-1] + theta * (mu - prices[i-1]) + sigma * np.random.normal()

    return _create_ohlcv(prices)


@pytest.fixture
def synthetic_random_walk_data():
    """Generate synthetic data with random walk behavior (H ≈ 0.5)"""
    np.random.seed(42)
    n = 500
    # Pure random walk
    returns = np.random.normal(0, 1, n)
    prices = 100 + np.cumsum(returns)

    return _create_ohlcv(prices)


@pytest.fixture
def edge_case_flat_prices():
    """Flat prices - tests division by zero handling"""
    n = 100
    prices = np.full(n, 100.0)
    return _create_ohlcv(prices)


@pytest.fixture
def edge_case_extreme_volatility():
    """Extreme price swings"""
    np.random.seed(42)
    n = 500
    prices = 100 + np.cumsum(np.random.normal(0, 50, n))  # High volatility
    prices = np.abs(prices) + 1  # Ensure positive
    return _create_ohlcv(prices)


@pytest.fixture
def edge_case_minimal_data():
    """Minimum viable data length"""
    prices = np.array([100, 101, 99, 102, 98, 103, 97, 104, 96, 105])
    return _create_ohlcv(prices)


@pytest.fixture
def edge_case_with_gaps():
    """Data with NaN values (gaps)"""
    np.random.seed(42)
    n = 500
    prices = 100 + np.cumsum(np.random.normal(0, 1, n))
    prices[50:55] = np.nan  # Introduce gap
    prices[200] = np.nan
    return _create_ohlcv(prices)


def _create_ohlcv(close_prices):
    """Helper to create OHLCV DataFrame from close prices"""
    n = len(close_prices)
    np.random.seed(123)  # Consistent OHLC generation

    # Handle NaN values in close prices
    close_clean = np.where(np.isnan(close_prices), 100.0, close_prices)

    df = pd.DataFrame({
        'open': close_clean * np.random.uniform(0.995, 1.005, n),
        'high': close_clean * np.random.uniform(1.001, 1.02, n),
        'low': close_clean * np.random.uniform(0.98, 0.999, n),
        'close': close_prices,
        'volume': np.random.uniform(1000, 10000, n)
    })

    # Ensure high >= close >= low (for non-NaN values)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    df.index = pd.date_range(start='2024-01-01', periods=n, freq='1h')
    return df
