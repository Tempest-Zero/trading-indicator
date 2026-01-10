"""
White-box tests for Kalman Filter.
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_engine.core.kalman import kalman_smooth, adaptive_kalman


class TestKalmanFilter:
    """White-box tests for Kalman Filter"""

    # ============ CORRECTNESS TESTS ============

    def test_kalman_smooths_noisy_data(self, synthetic_trending_data):
        """Kalman output should be smoother than input"""
        prices = synthetic_trending_data['close'].values
        result = kalman_smooth(prices)

        # Calculate roughness (sum of squared second differences)
        raw_roughness = np.sum(np.diff(prices, n=2)**2)
        kalman_roughness = np.sum(np.diff(result['filtered_price'], n=2)**2)

        assert kalman_roughness < raw_roughness, "Kalman should smooth the data"

    def test_kalman_tracks_trend(self, synthetic_trending_data):
        """Kalman velocity should be positive for uptrend"""
        prices = synthetic_trending_data['close'].values
        result = kalman_smooth(prices)

        # Average velocity in second half should be positive
        avg_velocity = np.mean(result['velocity'][250:])

        assert avg_velocity > 0, "Velocity should be positive in uptrend"

    def test_kalman_velocity_sign_matches_direction(self):
        """Velocity sign should match price direction"""
        # Strong uptrend
        prices_up = np.linspace(100, 200, 100)
        result_up = kalman_smooth(prices_up)
        assert np.mean(result_up['velocity'][50:]) > 0

        # Strong downtrend
        prices_down = np.linspace(200, 100, 100)
        result_down = kalman_smooth(prices_down)
        assert np.mean(result_down['velocity'][50:]) < 0

    def test_kalman_reduces_lag_vs_ema(self, synthetic_trending_data):
        """Kalman should track price at least as well as EMA"""
        prices = synthetic_trending_data['close'].values
        result = kalman_smooth(prices)

        # Calculate EMA for comparison
        alpha = 2 / 21  # 20-period EMA
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]

        # Correlation with price (higher = less lag)
        corr_kalman = np.corrcoef(prices[50:], result['filtered_price'][50:])[0, 1]
        corr_ema = np.corrcoef(prices[50:], ema[50:])[0, 1]

        # Kalman should track price at least as well as EMA
        assert corr_kalman >= corr_ema * 0.95, "Kalman should track as well as EMA"

    # ============ OUTPUT STRUCTURE TESTS ============

    def test_kalman_output_keys(self, synthetic_trending_data):
        """Kalman should return expected keys"""
        prices = synthetic_trending_data['close'].values
        result = kalman_smooth(prices)

        expected_keys = ['filtered_price', 'velocity', 'acceleration', 'uncertainty']
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_kalman_output_lengths(self, synthetic_trending_data):
        """All outputs should have same length as input"""
        prices = synthetic_trending_data['close'].values
        result = kalman_smooth(prices)

        for key, value in result.items():
            assert len(value) == len(prices), f"{key} length mismatch"

    def test_kalman_no_nans_in_output(self, synthetic_trending_data):
        """Output should not contain NaNs (given clean input)"""
        prices = synthetic_trending_data['close'].values
        result = kalman_smooth(prices)

        for key, value in result.items():
            assert not np.any(np.isnan(value)), f"NaN found in {key}"

    # ============ EDGE CASE TESTS ============

    def test_kalman_flat_prices(self, edge_case_flat_prices):
        """Flat prices should produce zero velocity"""
        prices = edge_case_flat_prices['close'].values
        result = kalman_smooth(prices)

        # Velocity should converge to near zero
        assert np.abs(result['velocity'][-1]) < 0.1

    def test_kalman_single_spike(self):
        """Single spike should be filtered out"""
        prices = np.full(100, 100.0)
        prices[50] = 150  # Spike

        result = kalman_smooth(prices)

        # Filtered price at spike should be much less than raw
        assert result['filtered_price'][50] < 145
        assert result['filtered_price'][50] > 100

    def test_kalman_step_change(self):
        """Step change should be tracked with some lag"""
        prices = np.concatenate([np.full(50, 100), np.full(50, 110)])
        result = kalman_smooth(prices)

        # Should eventually reach new level
        assert result['filtered_price'][-1] > 109

        # Should have lag at transition
        assert result['filtered_price'][50] < 110
        assert result['filtered_price'][50] > 100

    def test_kalman_parameter_sensitivity(self, synthetic_trending_data):
        """Different parameters should produce different smoothness"""
        prices = synthetic_trending_data['close'].values

        result_smooth = kalman_smooth(prices, transition_covariance=0.001)
        result_responsive = kalman_smooth(prices, transition_covariance=0.1)

        # Calculate roughness
        rough_smooth = np.sum(np.diff(result_smooth['filtered_price'])**2)
        rough_responsive = np.sum(np.diff(result_responsive['filtered_price'])**2)

        assert rough_smooth < rough_responsive, "Lower transition cov should be smoother"

    # ============ ADAPTIVE KALMAN TESTS ============

    def test_adaptive_kalman_volatility_response(self, edge_case_extreme_volatility):
        """Adaptive Kalman should work with volatility input"""
        prices = edge_case_extreme_volatility['close'].values
        volatility = pd.Series(prices).rolling(20).std().fillna(1).values

        result = adaptive_kalman(prices, volatility)

        assert 'filtered_price' in result
        assert 'velocity' in result
        assert len(result['filtered_price']) == len(prices)
