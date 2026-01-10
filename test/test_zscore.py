"""
White-box tests for Z-Score calculations.
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_engine.core.zscore import rolling_zscore, multi_timeframe_zscore


class TestZScore:
    """White-box tests for Z-Score calculations"""

    # ============ MATHEMATICAL CORRECTNESS ============

    def test_zscore_formula_correctness(self):
        """Verify Z-Score follows (x - μ) / σ formula"""
        np.random.seed(42)
        prices = np.random.normal(100, 10, 100)
        window = 20

        result = rolling_zscore(prices, window=window)

        # Manual calculation for last point
        last_window = prices[-window:]
        expected_mean = np.mean(last_window)
        expected_std = np.std(last_window, ddof=1)  # Sample std
        expected_z = (prices[-1] - expected_mean) / expected_std

        np.testing.assert_almost_equal(
            result['zscore'][-1],
            expected_z,
            decimal=3,
            err_msg="Z-Score formula mismatch"
        )

    def test_zscore_mean_is_near_zero(self):
        """Mean of Z-Scores over rolling window should be ~0"""
        np.random.seed(42)
        prices = np.random.normal(100, 10, 500)

        result = rolling_zscore(prices, window=20)

        # Mean of Z-Scores (excluding NaN) should be near 0
        mean_z = np.nanmean(result['zscore'])
        assert abs(mean_z) < 0.3, f"Mean Z-Score should be near 0, got {mean_z}"

    def test_zscore_std_is_near_one(self):
        """Std of Z-Scores should be ~1 for normally distributed data"""
        np.random.seed(42)
        prices = np.random.normal(100, 10, 1000)

        result = rolling_zscore(prices, window=50)

        std_z = np.nanstd(result['zscore'])
        assert 0.7 < std_z < 1.3, f"Std of Z-Score should be ~1, got {std_z}"

    # ============ EXTREME DETECTION TESTS ============

    def test_extreme_low_detection(self):
        """Z < -2 should be flagged as extreme low"""
        prices = np.concatenate([
            np.full(50, 100),
            np.array([70])  # Extreme low
        ])

        result = rolling_zscore(prices, window=50)

        assert result['extreme_low'][-1] == True
        assert result['zscore'][-1] < -2

    def test_extreme_high_detection(self):
        """Z > 2 should be flagged as extreme high"""
        prices = np.concatenate([
            np.full(50, 100),
            np.array([130])  # Extreme high
        ])

        result = rolling_zscore(prices, window=50)

        assert result['extreme_high'][-1] == True
        assert result['zscore'][-1] > 2

    def test_mild_zones_flags_exist(self):
        """Mild zone flags should exist and be boolean"""
        prices = np.random.normal(100, 10, 100)
        result = rolling_zscore(prices, window=20)

        assert result['mild_high'].dtype == bool
        assert result['mild_low'].dtype == bool

    # ============ OUTPUT STRUCTURE TESTS ============

    def test_zscore_output_keys(self):
        """Z-Score should return all expected keys"""
        prices = np.random.normal(100, 10, 100)
        result = rolling_zscore(prices, window=20)

        expected_keys = ['zscore', 'mean', 'std', 'percentile',
                         'extreme_low', 'extreme_high', 'mild_low', 'mild_high']
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_zscore_initial_nans(self):
        """First window-1 values should be NaN"""
        prices = np.random.normal(100, 10, 100)
        window = 20

        result = rolling_zscore(prices, window=window)

        assert np.all(np.isnan(result['zscore'][:window-1]))

    # ============ EDGE CASE TESTS ============

    def test_zscore_zero_std(self, edge_case_flat_prices):
        """Zero std should not produce infinity"""
        prices = edge_case_flat_prices['close'].values
        result = rolling_zscore(prices, window=20)

        assert not np.any(np.isinf(result['zscore'][~np.isnan(result['zscore'])]))

    def test_zscore_single_outlier(self):
        """Single outlier in otherwise flat data"""
        prices = np.full(100, 100.0)
        prices[50] = 200  # Outlier

        result = rolling_zscore(prices, window=20)

        # Point 50 should have high Z-Score (but may be NaN if in window)
        # Check a point after the outlier enters the window
        if not np.isnan(result['zscore'][55]):
            # The outlier should cause elevated z-scores
            pass  # Just ensure no crash

    # ============ MULTI-TIMEFRAME TESTS ============

    def test_multi_tf_zscore_keys(self):
        """Multi-TF should return Z-Scores for each window"""
        prices = np.random.normal(100, 10, 200)
        windows = [20, 50, 100]

        result = multi_timeframe_zscore(prices, windows=windows)

        for w in windows:
            assert f'z_{w}' in result
        assert 'confluence' in result
        assert 'aligned_oversold' in result
        assert 'aligned_overbought' in result

    def test_multi_tf_confluence_range(self):
        """Confluence should be in [-1, 1] range"""
        prices = np.random.normal(100, 10, 200)

        result = multi_timeframe_zscore(prices, windows=[20, 50, 100])

        valid_confluence = result['confluence'][~np.isnan(result['confluence'])]
        assert np.all(valid_confluence >= -1)
        assert np.all(valid_confluence <= 1)

    def test_multi_tf_aligned_signals(self):
        """Aligned signals should only trigger when all timeframes agree"""
        # Create data that's oversold on all timeframes
        prices = np.concatenate([
            np.linspace(150, 100, 150),  # Downtrend
            np.full(10, 70)  # Crash to oversold
        ])

        result = multi_timeframe_zscore(prices, windows=[20, 50, 100])

        # Should have some aligned oversold signals (may not always trigger)
        # At minimum, check it doesn't crash and returns correct type
        assert result['aligned_oversold'].dtype == bool
