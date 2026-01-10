"""
White-box tests for volume analysis.
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_engine.core.volume import volume_delta, volume_profile


class TestVolumeAnalysis:
    """White-box tests for volume analysis"""

    # ============ VOLUME DELTA TESTS ============

    def test_bullish_candle_positive_delta(self):
        """Bullish candle (close near high) should have positive delta"""
        ohlcv = pd.DataFrame({
            'open': [100],
            'high': [110],
            'low': [99],
            'close': [109],  # Close near high = bullish
            'volume': [1000]
        })

        result = volume_delta(ohlcv)

        assert result['delta'][0] > 0, "Bullish candle should have positive delta"
        assert result['buying_pressure'][0] == True

    def test_bearish_candle_negative_delta(self):
        """Bearish candle (close near low) should have negative delta"""
        ohlcv = pd.DataFrame({
            'open': [105],
            'high': [106],
            'low': [95],
            'close': [96],  # Close near low = bearish
            'volume': [1000]
        })

        result = volume_delta(ohlcv)

        assert result['delta'][0] < 0, "Bearish candle should have negative delta"
        assert result['selling_pressure'][0] == True

    def test_doji_candle_neutral_delta(self):
        """Doji (close in middle) should have near-zero delta"""
        ohlcv = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [100],  # Close in middle
            'volume': [1000]
        })

        result = volume_delta(ohlcv)

        assert abs(result['delta'][0]) < 100, "Doji should have small delta"

    def test_volume_delta_sums_to_total(self):
        """Buy volume + sell volume should equal total volume"""
        np.random.seed(42)
        ohlcv = pd.DataFrame({
            'open': np.random.uniform(99, 101, 100),
            'high': np.random.uniform(101, 105, 100),
            'low': np.random.uniform(95, 99, 100),
            'close': np.random.uniform(97, 103, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        })
        # Fix high/low
        ohlcv['high'] = ohlcv[['open', 'high', 'close']].max(axis=1)
        ohlcv['low'] = ohlcv[['open', 'low', 'close']].min(axis=1)

        result = volume_delta(ohlcv)

        total = result['buy_volume'] + result['sell_volume']
        np.testing.assert_array_almost_equal(total, ohlcv['volume'].values)

    def test_cumulative_delta_is_cumsum(self):
        """Cumulative delta should be cumsum of delta"""
        np.random.seed(42)
        ohlcv = pd.DataFrame({
            'open': np.random.uniform(99, 101, 50),
            'high': np.random.uniform(101, 105, 50),
            'low': np.random.uniform(95, 99, 50),
            'close': np.random.uniform(97, 103, 50),
            'volume': np.random.uniform(1000, 5000, 50)
        })
        ohlcv['high'] = ohlcv[['open', 'high', 'close']].max(axis=1)
        ohlcv['low'] = ohlcv[['open', 'low', 'close']].min(axis=1)

        result = volume_delta(ohlcv)

        expected_cumulative = np.cumsum(result['delta'])
        np.testing.assert_array_almost_equal(
            result['cumulative_delta'],
            expected_cumulative
        )

    # ============ EDGE CASES ============

    def test_zero_range_candle(self):
        """Zero range candle (high == low) should not crash"""
        ohlcv = pd.DataFrame({
            'open': [100],
            'high': [100],
            'low': [100],
            'close': [100],
            'volume': [1000]
        })

        result = volume_delta(ohlcv)

        assert not np.isnan(result['delta'][0])
        assert not np.isinf(result['delta'][0])

    def test_zero_volume(self):
        """Zero volume should not crash"""
        ohlcv = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [0]
        })

        result = volume_delta(ohlcv)

        assert result['delta'][0] == 0

    # ============ VOLUME PROFILE TESTS ============

    def test_volume_profile_poc_in_range(self, synthetic_trending_data):
        """POC should be within price range"""
        result = volume_profile(synthetic_trending_data)

        price_min = synthetic_trending_data['close'].min()
        price_max = synthetic_trending_data['close'].max()

        assert price_min <= result['poc'] <= price_max

    def test_value_area_contains_poc(self, synthetic_trending_data):
        """POC should be within value area"""
        result = volume_profile(synthetic_trending_data)

        assert result['value_area_low'] <= result['poc'] <= result['value_area_high']

    def test_value_area_ordering(self, synthetic_trending_data):
        """Value area low should be less than high"""
        result = volume_profile(synthetic_trending_data)

        assert result['value_area_low'] < result['value_area_high']

    def test_volume_profile_bins_sum(self, synthetic_trending_data):
        """Volume at all levels should sum to total volume"""
        result = volume_profile(synthetic_trending_data, num_bins=20)

        total_volume = synthetic_trending_data['volume'].sum()
        binned_volume = result['volume_at_level'].sum()

        np.testing.assert_almost_equal(total_volume, binned_volume, decimal=0)
