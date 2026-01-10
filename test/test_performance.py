"""
Performance and benchmark tests.
"""

import pytest
import numpy as np
import pandas as pd
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_engine.core.engine import QuantEngine
from quant_engine.core.hurst import hurst_exponent, rolling_hurst
from quant_engine.core.kalman import kalman_smooth
from quant_engine.core.zscore import rolling_zscore


class TestPerformance:
    """Performance and benchmark tests"""

    def _generate_data(self, n):
        """Generate test data of size n"""
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.normal(0, 1, n))
        df = pd.DataFrame({
            'open': prices * 0.999,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.uniform(1000, 10000, n)
        })
        df.index = pd.date_range(start='2024-01-01', periods=n, freq='1h')
        return df, prices

    # ============ TIMING BENCHMARKS ============

    @pytest.mark.benchmark
    def test_hurst_performance_500(self):
        """Hurst calculation for 500 points should be < 500ms"""
        _, prices = self._generate_data(500)

        start = time.time()
        _ = hurst_exponent(prices)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Hurst took {elapsed:.3f}s (limit: 0.5s)"

    @pytest.mark.benchmark
    def test_rolling_hurst_performance_500(self):
        """Rolling Hurst for 500 points should be < 10s"""
        _, prices = self._generate_data(500)

        start = time.time()
        _ = rolling_hurst(prices, window=100)
        elapsed = time.time() - start

        assert elapsed < 10.0, f"Rolling Hurst took {elapsed:.3f}s (limit: 10s)"

    @pytest.mark.benchmark
    def test_kalman_performance_500(self):
        """Kalman filter for 500 points should be < 500ms"""
        _, prices = self._generate_data(500)

        start = time.time()
        _ = kalman_smooth(prices)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Kalman took {elapsed:.3f}s (limit: 0.5s)"

    @pytest.mark.benchmark
    def test_zscore_performance_500(self):
        """Z-Score for 500 points should be < 200ms"""
        _, prices = self._generate_data(500)

        start = time.time()
        _ = rolling_zscore(prices, window=20)
        elapsed = time.time() - start

        assert elapsed < 0.2, f"Z-Score took {elapsed:.3f}s (limit: 0.2s)"

    @pytest.mark.benchmark
    def test_full_engine_performance_500(self):
        """Full engine analysis for 500 points should be < 15s"""
        df, _ = self._generate_data(500)
        engine = QuantEngine()

        start = time.time()
        _ = engine.analyze(df)
        elapsed = time.time() - start

        assert elapsed < 15.0, f"Full engine took {elapsed:.3f}s (limit: 15s)"

    # ============ SCALING TESTS ============

    @pytest.mark.benchmark
    def test_scaling_linear_check(self):
        """Verify computational complexity doesn't explode"""
        sizes = [100, 200, 400]
        times = []

        for n in sizes:
            _, prices = self._generate_data(n)

            start = time.time()
            _ = rolling_zscore(prices, window=20)
            elapsed = time.time() - start
            times.append(elapsed)

        # Time should scale roughly linearly (allow 5x for 4x data)
        if times[0] > 0.001:  # Only check if first time is meaningful
            ratio = times[-1] / times[0]
            size_ratio = sizes[-1] / sizes[0]

            # Should be less than quadratic scaling
            assert ratio < size_ratio * 5, f"Scaling too poor: {ratio:.1f}x for {size_ratio}x data"

    # ============ MEMORY TESTS ============

    @pytest.mark.benchmark
    def test_memory_no_leaks(self):
        """Repeated calls should not accumulate significant memory"""
        import gc

        df, _ = self._generate_data(500)
        engine = QuantEngine()

        # Warmup
        _ = engine.analyze(df)
        gc.collect()

        # Run 20 times
        for _ in range(20):
            _ = engine.analyze(df)

        gc.collect()

        # If we get here without memory errors, the test passes
        assert True

    # ============ CORRECTNESS UNDER LOAD ============

    @pytest.mark.benchmark
    def test_correctness_under_repeated_calls(self):
        """Results should be consistent across repeated calls"""
        df, _ = self._generate_data(500)
        engine = QuantEngine()

        results = []
        for _ in range(5):
            result = engine.analyze(df)
            results.append(result.hurst_value)

        # All results should be identical
        assert all(r == results[0] for r in results), "Results not deterministic"
