"""
Quant Market Analysis Engine

A sophisticated quantitative analysis framework for market analysis.
Uses Hurst Exponent for regime detection, Kalman Filter for noise reduction,
Z-Score for statistical triggers, and Volume analysis for confirmation.
"""

from quant_engine.core.engine import QuantEngine, MarketConditions

__version__ = "1.0.0"
__all__ = ["QuantEngine", "MarketConditions"]
