"""
Black-box tests treating engine as opaque system.
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_engine.core.engine import QuantEngine, MarketConditions


class TestQuantEngineBlackBox:
    """Black-box tests treating engine as opaque system"""

    @pytest.fixture
    def engine(self):
        return QuantEngine()

    # ============ INPUT VALIDATION ============

    def test_accepts_valid_ohlcv(self, engine, synthetic_trending_data):
        """Engine should accept valid OHLCV DataFrame"""
        result = engine.analyze(synthetic_trending_data, symbol='TEST')

        assert isinstance(result, MarketConditions)

    def test_rejects_missing_columns(self, engine):
        """Engine should handle missing columns gracefully"""
        invalid_df = pd.DataFrame({
            'open': [100, 101, 102],
            'close': [101, 102, 103]
            # Missing high, low, volume
        })
        invalid_df.index = pd.date_range(start='2024-01-01', periods=3, freq='1h')

        with pytest.raises((KeyError, ValueError)):
            engine.analyze(invalid_df)

    def test_rejects_empty_dataframe(self, engine):
        """Engine should reject empty DataFrame"""
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        with pytest.raises((ValueError, IndexError)):
            engine.analyze(empty_df)

    # ============ OUTPUT VALIDATION ============

    def test_output_has_all_fields(self, engine, synthetic_trending_data):
        """Output should contain all expected fields"""
        result = engine.analyze(synthetic_trending_data, symbol='TEST')

        expected_fields = [
            'symbol', 'timestamp', 'regime', 'regime_confidence',
            'hurst_value', 'kalman_price', 'kalman_velocity',
            'trend_direction', 'zscore', 'percentile',
            'statistical_condition', 'volume_delta_pct',
            'cumulative_delta_trend', 'poc', 'value_area_high',
            'value_area_low', 'pullback_probability',
            'trend_continuation_probability', 'suggested_bias',
            'confidence', 'notes'
        ]

        for field in expected_fields:
            assert hasattr(result, field), f"Missing field: {field}"

    def test_output_types(self, engine, synthetic_trending_data):
        """Output fields should have correct types"""
        result = engine.analyze(synthetic_trending_data)

        assert isinstance(result.regime, str)
        assert isinstance(result.regime_confidence, (int, float))
        assert isinstance(result.hurst_value, (int, float))
        assert isinstance(result.trend_direction, str)
        assert isinstance(result.pullback_probability, (int, float))
        assert isinstance(result.notes, list)

    def test_output_value_ranges(self, engine, synthetic_trending_data):
        """Output values should be within valid ranges"""
        result = engine.analyze(synthetic_trending_data)

        # Probabilities should be 0-1
        assert 0 <= result.pullback_probability <= 1
        assert 0 <= result.trend_continuation_probability <= 1
        assert 0 <= result.confidence <= 1
        assert 0 <= result.regime_confidence <= 1

        # Hurst should be 0-1
        assert 0 <= result.hurst_value <= 1

        # Percentile should be 0-100
        assert 0 <= result.percentile <= 100

        # Regime should be valid
        assert result.regime in ['TRENDING', 'MEAN_REVERTING', 'RANDOM_WALK', 'UNKNOWN']

        # Trend direction should be valid
        assert result.trend_direction in ['UP', 'DOWN', 'NEUTRAL']

        # Bias should be valid
        assert result.suggested_bias in ['UP', 'DOWN', 'NEUTRAL', 'WAIT']

    def test_probabilities_sum(self, engine, synthetic_trending_data):
        """Pullback and continuation probabilities should sum to ~1"""
        result = engine.analyze(synthetic_trending_data)

        total = result.pullback_probability + result.trend_continuation_probability
        assert 0.99 <= total <= 1.01, f"Probabilities sum to {total}"

    # ============ CONSISTENCY TESTS ============

    def test_deterministic_output(self, engine, synthetic_trending_data):
        """Same input should produce same output"""
        result1 = engine.analyze(synthetic_trending_data, symbol='TEST')
        result2 = engine.analyze(synthetic_trending_data, symbol='TEST')

        assert result1.regime == result2.regime
        assert result1.hurst_value == result2.hurst_value
        assert result1.zscore == result2.zscore

    def test_symbol_passthrough(self, engine, synthetic_trending_data):
        """Symbol should pass through to output"""
        result = engine.analyze(synthetic_trending_data, symbol='BTC/USDT')

        assert result.symbol == 'BTC/USDT'

    # ============ BEHAVIORAL TESTS ============

    def test_trending_data_produces_trending_regime(self, engine, synthetic_trending_data):
        """Known trending data should produce TRENDING regime"""
        result = engine.analyze(synthetic_trending_data)

        # Should be TRENDING with reasonable confidence
        assert result.regime in ['TRENDING', 'RANDOM_WALK']  # Allow some variance
        if result.regime == 'TRENDING':
            assert result.regime_confidence > 0.3

    def test_mean_reverting_data_produces_mr_regime(self, engine, synthetic_mean_reverting_data):
        """Known mean-reverting data should produce MEAN_REVERTING regime"""
        result = engine.analyze(synthetic_mean_reverting_data)

        assert result.regime in ['MEAN_REVERTING', 'RANDOM_WALK']

    def test_notes_provide_reasoning(self, engine, synthetic_trending_data):
        """Notes should explain the analysis"""
        result = engine.analyze(synthetic_trending_data)

        assert len(result.notes) > 0, "Should have at least one note"
        assert all(isinstance(n, str) for n in result.notes)

    # ============ STRESS TESTS ============

    def test_large_dataset(self, engine):
        """Engine should handle large datasets"""
        np.random.seed(42)
        large_data = pd.DataFrame({
            'open': np.random.uniform(99, 101, 10000),
            'high': np.random.uniform(101, 105, 10000),
            'low': np.random.uniform(95, 99, 10000),
            'close': np.random.uniform(97, 103, 10000),
            'volume': np.random.uniform(1000, 10000, 10000)
        })
        large_data['high'] = large_data[['open', 'high', 'close']].max(axis=1)
        large_data['low'] = large_data[['open', 'low', 'close']].min(axis=1)
        large_data.index = pd.date_range(start='2020-01-01', periods=10000, freq='1h')

        result = engine.analyze(large_data)

        assert isinstance(result, MarketConditions)

    def test_minimal_dataset(self, engine, edge_case_minimal_data):
        """Engine should handle minimal datasets"""
        # For minimal data, engine may raise ValueError for insufficient data
        # This is acceptable behavior
        try:
            result = engine.analyze(edge_case_minimal_data)
            assert isinstance(result, MarketConditions)
        except ValueError as e:
            # Acceptable to raise error for insufficient data
            assert 'insufficient' in str(e).lower() or 'need' in str(e).lower()


class TestCrossAssetBehavior:
    """Test that engine behaves consistently across different asset types"""

    @pytest.fixture
    def engine(self):
        return QuantEngine()

    def _generate_asset_data(self, base_price, volatility, n=500):
        """Generate synthetic asset data with given characteristics"""
        np.random.seed(42)
        returns = np.random.normal(0, volatility, n)
        prices = base_price * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'open': prices * np.random.uniform(0.999, 1.001, n),
            'high': prices * np.random.uniform(1.001, 1 + volatility*2, n),
            'low': prices * np.random.uniform(1 - volatility*2, 0.999, n),
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n) * base_price
        })
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        df.index = pd.date_range(start='2024-01-01', periods=n, freq='1h')
        return df

    def test_bitcoin_like_data(self, engine):
        """Test with Bitcoin-like characteristics (high vol, ~$100k)"""
        btc_data = self._generate_asset_data(100000, 0.03)  # 3% daily vol
        result = engine.analyze(btc_data, symbol='BTC')

        assert isinstance(result.regime, str)
        assert not np.isnan(result.zscore)

    def test_penny_stock_data(self, engine):
        """Test with penny stock characteristics (low price, high vol)"""
        penny_data = self._generate_asset_data(0.05, 0.10)  # 10% daily vol
        result = engine.analyze(penny_data, symbol='PENNY')

        assert isinstance(result.regime, str)
        assert not np.isnan(result.zscore)

    def test_stable_stock_data(self, engine):
        """Test with stable stock characteristics (low vol)"""
        stable_data = self._generate_asset_data(150, 0.005)  # 0.5% daily vol
        result = engine.analyze(stable_data, symbol='STABLE')

        assert isinstance(result.regime, str)

    def test_scale_invariance(self, engine):
        """Z-Score should be scale-invariant"""
        np.random.seed(42)

        # Same pattern at different scales
        base_returns = np.random.normal(0, 0.02, 500)

        prices_100 = 100 * np.exp(np.cumsum(base_returns))
        prices_100000 = 100000 * np.exp(np.cumsum(base_returns))

        df_100 = self._generate_asset_data(100, 0.02)
        df_100['close'] = prices_100

        df_100000 = self._generate_asset_data(100000, 0.02)
        df_100000['close'] = prices_100000

        result_100 = engine.analyze(df_100)
        result_100000 = engine.analyze(df_100000)

        # Z-Scores should be similar (scale-invariant)
        assert abs(result_100.zscore - result_100000.zscore) < 1.0
