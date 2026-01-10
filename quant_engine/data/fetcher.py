"""
Data Fetcher Module

Unified data fetcher for stocks and cryptocurrency OHLCV data.
Supports yfinance for stocks and ccxt for crypto exchanges.
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime, timedelta


class DataFetcher:
    """
    Unified data fetcher for stocks and crypto.

    Automatically detects the asset type based on symbol format:
    - Crypto pairs contain '/' (e.g., 'BTC/USDT')
    - Stock tickers are plain symbols (e.g., 'AAPL', 'SPY')

    Example usage:
        fetcher = DataFetcher()
        df = fetcher.get_ohlcv('BTC/USDT', timeframe='1h', limit=500)
        df = fetcher.get_ohlcv('AAPL', timeframe='1d', limit=200)
    """

    def __init__(self, exchange: str = 'binance'):
        """
        Initialize the data fetcher.

        Args:
            exchange: Default crypto exchange to use (binance, coinbase, kraken, etc.)
        """
        self.default_exchange = exchange
        self._ccxt_exchange = None

    def get_ohlcv(self,
                  symbol: str,
                  timeframe: str = '1h',
                  limit: int = 500,
                  exchange: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch OHLCV data from appropriate source.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT') or stock ticker (e.g., 'AAPL')
            timeframe: Candlestick timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch
            exchange: Crypto exchange override (only for crypto pairs)

        Returns:
            DataFrame with columns [open, high, low, close, volume]
            Index is datetime
        """
        if '/' in symbol:  # Crypto pair like BTC/USDT
            return self._fetch_crypto(symbol, timeframe, limit, exchange)
        else:  # Stock ticker
            return self._fetch_stock(symbol, timeframe, limit)

    def _fetch_crypto(self,
                      symbol: str,
                      timeframe: str,
                      limit: int,
                      exchange: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch cryptocurrency OHLCV data using ccxt.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candlestick timeframe
            limit: Number of candles
            exchange: Exchange name override

        Returns:
            DataFrame with OHLCV data
        """
        try:
            import ccxt
        except ImportError:
            raise ImportError(
                "ccxt is required for crypto data. Install with: pip install ccxt"
            )

        exchange_name = exchange or self.default_exchange

        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_name)
        ex = exchange_class({
            'enableRateLimit': True,
        })

        # Fetch OHLCV data
        ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)

        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.set_index('timestamp')

        return df

    def _fetch_stock(self,
                     symbol: str,
                     timeframe: str,
                     limit: int) -> pd.DataFrame:
        """
        Fetch stock OHLCV data using yfinance.

        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            timeframe: Candlestick timeframe
            limit: Number of candles

        Returns:
            DataFrame with OHLCV data
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError(
                "yfinance is required for stock data. Install with: pip install yfinance"
            )

        # Map timeframe to yfinance interval
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '1h',  # yfinance doesn't support 4h, we'll resample
            '1d': '1d',
            '1w': '1wk',
            '1M': '1mo',
        }

        interval = interval_map.get(timeframe, '1h')

        # Determine period based on interval and limit
        period_map = {
            '1m': '7d',
            '5m': '60d',
            '15m': '60d',
            '30m': '60d',
            '1h': '730d',
            '1d': 'max',
            '1wk': 'max',
            '1mo': 'max',
        }

        period = period_map.get(interval, '60d')

        # Fetch data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        # Normalize column names
        df.columns = [c.lower() for c in df.columns]

        # Select only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']]

        # Handle 4h timeframe by resampling
        if timeframe == '4h' and interval == '1h':
            df = df.resample('4h').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()

        # Return the last 'limit' rows
        return df.tail(limit)

    def get_multiple(self,
                     symbols: list,
                     timeframe: str = '1h',
                     limit: int = 500) -> dict:
        """
        Fetch OHLCV data for multiple symbols.

        Args:
            symbols: List of symbols
            timeframe: Candlestick timeframe
            limit: Number of candles

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        data = {}
        for symbol in symbols:
            try:
                data[symbol] = self.get_ohlcv(symbol, timeframe, limit)
            except Exception as e:
                print(f"Warning: Failed to fetch {symbol}: {e}")
                data[symbol] = None
        return data


def generate_sample_data(n_bars: int = 500,
                         volatility: float = 0.02,
                         trend: float = 0.0001,
                         seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for testing.

    Args:
        n_bars: Number of bars to generate
        volatility: Daily volatility (standard deviation of returns)
        trend: Daily drift/trend
        seed: Random seed for reproducibility

    Returns:
        DataFrame with OHLCV data
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate returns with trend and volatility
    returns = np.random.normal(trend, volatility, n_bars)

    # Generate close prices
    close = 100 * np.exp(np.cumsum(returns))

    # Generate OHLC from close
    high_delta = np.abs(np.random.normal(0, volatility, n_bars))
    low_delta = np.abs(np.random.normal(0, volatility, n_bars))

    high = close * (1 + high_delta)
    low = close * (1 - low_delta)

    # Open is previous close with noise
    open_prices = np.roll(close, 1) * (1 + np.random.normal(0, volatility/5, n_bars))
    open_prices[0] = close[0] * (1 - np.random.uniform(0, volatility))

    # Ensure OHLC consistency
    high = np.maximum(high, np.maximum(open_prices, close))
    low = np.minimum(low, np.minimum(open_prices, close))

    # Generate volume
    base_volume = 1000000
    volume = base_volume * np.exp(np.random.normal(0, 0.5, n_bars))

    # Create DataFrame
    dates = pd.date_range(end=datetime.now(), periods=n_bars, freq='h')

    df = pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)

    return df
