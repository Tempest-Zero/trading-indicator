"""
White-box tests for Hurst Exponent calculation.
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_engine.core.hurst import hurst_exponent, rolling_hurst, classify_regime


class TestHurstExponent:
    """White-box tests for Hurst Exponent calculation"""

    # ============ CORRECTNESS TESTS ============

    def test_trending_data_returns_high_hurst(self, synthetic_trending_data):
        """Trending data should produce H > 0.5"""
        prices = synthetic_trending_data['close'].values
        h = hurst_exponent(prices)

        assert h > 0.5, f"Trending data should have H > 0.5, got {h}"
        assert h < 1.0, f"Hurst should be < 1.0, got {h}"

    def test_mean_reverting_data_returns_low_hurst(self, synthetic_mean_reverting_data):
        """Mean-reverting data should produce H < 0.5"""
        prices = synthetic_mean_reverting_data['close'].values
        h = hurst_exponent(prices)

        assert h < 0.5, f"Mean-reverting data should have H < 0.5, got {h}"
        assert h > 0.0, f"Hurst should be > 0.0, got {h}"

    def test_random_walk_returns_near_half(self, synthetic_random_walk_data):
        """Random walk should produce H ≈ 0.5"""
        prices = synthetic_random_walk_data['close'].values
        h = hurst_exponent(prices)

        assert 0.35 < h < 0.65, f"Random walk should have H ≈ 0.5, got {h}"

    def test_known_hurst_series(self):
        """Test against mathematically constructed series with known H"""
        np.random.seed(123)
        n = 1000

        # Construct persistent series (H > 0.5)
        # Method: Use positively correlated increments
        increments = np.random.normal(0, 1, n)
        for i in range(1, n):
            increments[i] += 0.3 * increments[i-1]  # Positive autocorrelation
        prices = 100 + np.cumsum(increments)

        h = hurst_exponent(prices)
        assert h > 0.5, f"Persistent series should have H > 0.5, got {h}"

    # ============ EDGE CASE TESTS ============

    def test_flat_prices_returns_valid_hurst(self, edge_case_flat_prices):
        """Flat prices should not crash, should return ~0.5 or handle gracefully"""
        prices = edge_case_flat_prices['close'].values
        h = hurst_exponent(prices)

        assert not np.isnan(h), "Hurst should not be NaN for flat prices"
        assert not np.isinf(h), "Hurst should not be infinite for flat prices"

    def test_minimal_data_length(self):
        """Test with minimum data length"""
        prices = np.array([100, 101, 99, 102, 98])
        h = hurst_exponent(prices, max_lag=3)

        # Should either return valid value or 0.5 (insufficient data)
        assert 0 <= h <= 1 or h == 0.5

    def test_single_price_point(self):
        """Single price point should handle gracefully"""
        prices = np.array([100])
        h = hurst_exponent(prices)

        assert h == 0.5, "Single point should return default 0.5"

    def test_two_price_points(self):
        """Two price points - minimal case"""
        prices = np.array([100, 105])
        h = hurst_exponent(prices, max_lag=2)

        assert not np.isnan(h)

    def test_negative_prices(self):
        """Negative prices (allowed in some instruments)"""
        np.random.seed(42)
        prices = -50 + np.cumsum(np.random.normal(0, 1, 100))
        h = hurst_exponent(prices)

        assert 0 < h < 1, "Should handle negative prices"

    def test_extreme_values(self):
        """Very large and very small prices"""
        np.random.seed(42)
        # Large prices
        prices_large = 1e9 + np.cumsum(np.random.normal(0, 1e6, 200))
        h_large = hurst_exponent(prices_large)

        # Small prices
        prices_small = 0.0001 + np.abs(np.cumsum(np.random.normal(0, 0.00001, 200)))
        h_small = hurst_exponent(prices_small)

        assert 0 < h_large < 1
        assert 0 < h_small < 1

    # ============ ROLLING HURST TESTS ============

    def test_rolling_hurst_output_length(self, synthetic_trending_data):
        """Rolling Hurst output should match input length"""
        prices = synthetic_trending_data['close'].values
        window = 100

        rolling_h = rolling_hurst(prices, window=window)

        assert len(rolling_h) == len(prices)

    def test_rolling_hurst_initial_nans(self, synthetic_trending_data):
        """First 'window' values should be NaN"""
        prices = synthetic_trending_data['close'].values
        window = 100

        rolling_h = rolling_hurst(prices, window=window)

        assert np.all(np.isnan(rolling_h[:window]))
        assert not np.isnan(rolling_h[window])

    def test_rolling_hurst_smoothing(self, synthetic_trending_data):
        """Smoothed output should be less volatile than unsmoothed"""
        prices = synthetic_trending_data['close'].values

        unsmoothed = rolling_hurst(prices, window=100, smooth=1)
        smoothed = rolling_hurst(prices, window=100, smooth=20)

        # Compare variance of non-NaN values
        var_unsmoothed = np.nanvar(unsmoothed)
        var_smoothed = np.nanvar(smoothed)

        assert var_smoothed < var_unsmoothed, "Smoothing should reduce variance"

    # ============ REGIME CLASSIFICATION TESTS ============

    def test_classify_regime_trending(self):
        """H > 0.6 should classify as TRENDING"""
        result = classify_regime(0.7)

        assert result['regime'] == 'TRENDING'
        assert result['strategy'] == 'FOLLOW_MOMENTUM'
        assert result['confidence'] > 0

    def test_classify_regime_mean_reverting(self):
        """H < 0.4 should classify as MEAN_REVERTING"""
        result = classify_regime(0.3)

        assert result['regime'] == 'MEAN_REVERTING'
        assert result['strategy'] == 'FADE_EXTREMES'

    def test_classify_regime_random_walk(self):
        """H ≈ 0.5 should classify as RANDOM_WALK"""
        result = classify_regime(0.5)

        assert result['regime'] == 'RANDOM_WALK'
        assert result['strategy'] == 'REDUCE_RISK'

    def test_classify_regime_nan_input(self):
        """NaN input should return UNKNOWN"""
        result = classify_regime(np.nan)

        assert result['regime'] == 'UNKNOWN'
        assert result['confidence'] == 0

    def test_classify_regime_boundary_values(self):
        """Test boundary values 0.4, 0.6"""
        assert classify_regime(0.39)['regime'] == 'MEAN_REVERTING'
        assert classify_regime(0.40)['regime'] == 'RANDOM_WALK'  # Boundary
        assert classify_regime(0.60)['regime'] == 'RANDOM_WALK'  # Boundary
        assert classify_regime(0.61)['regime'] == 'TRENDING'
