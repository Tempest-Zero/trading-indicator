#!/usr/bin/env python3
"""
Quant Market Analysis Engine - Main Entry Point

Usage Examples:
    # Analyze crypto pair
    python -m quant_engine.main BTC/USDT --timeframe 1h

    # Analyze stock
    python -m quant_engine.main AAPL --timeframe 1d

    # Use sample data (no API required)
    python -m quant_engine.main --sample

    # Save dashboard to file
    python -m quant_engine.main BTC/USDT --output dashboard.html
"""

import argparse
import sys
from typing import Optional

import pandas as pd
import numpy as np


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Quant Market Analysis Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m quant_engine.main BTC/USDT --timeframe 1h
  python -m quant_engine.main AAPL --timeframe 1d --output chart.html
  python -m quant_engine.main --sample --show-chart
        """
    )

    parser.add_argument(
        'symbol',
        nargs='?',
        default=None,
        help='Trading pair (e.g., BTC/USDT) or stock ticker (e.g., AAPL)'
    )

    parser.add_argument(
        '--timeframe', '-t',
        default='1h',
        choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
        help='Candle timeframe (default: 1h)'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=500,
        help='Number of candles to fetch (default: 500)'
    )

    parser.add_argument(
        '--exchange', '-e',
        default='binance',
        help='Crypto exchange to use (default: binance)'
    )

    parser.add_argument(
        '--sample', '-s',
        action='store_true',
        help='Use sample data instead of fetching from API'
    )

    parser.add_argument(
        '--output', '-o',
        help='Save dashboard to file (HTML format)'
    )

    parser.add_argument(
        '--show-chart',
        action='store_true',
        help='Display interactive chart in browser'
    )

    parser.add_argument(
        '--format', '-f',
        default='text',
        choices=['text', 'markdown', 'json'],
        help='Output format for report (default: text)'
    )

    parser.add_argument(
        '--preset', '-p',
        default='default',
        choices=['default', 'fast', 'smooth', 'aggressive'],
        help='Analysis preset (default: default)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick scan mode (essential metrics only)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Import modules
    from quant_engine.core.engine import QuantEngine, create_engine
    from quant_engine.data.fetcher import DataFetcher, generate_sample_data
    from quant_engine.output.dashboard import (
        create_dashboard,
        print_summary,
        print_quick_summary,
        generate_report
    )

    # Validate arguments
    if args.symbol is None and not args.sample:
        print("Error: Please provide a symbol or use --sample for demo data")
        print("Example: python -m quant_engine.main BTC/USDT")
        sys.exit(1)

    # Get data
    if args.sample:
        print("Using sample data for demonstration...")
        ohlcv = generate_sample_data(n_bars=args.limit, seed=42)
        symbol = "SAMPLE"
    else:
        print(f"Fetching {args.symbol} data from {args.exchange}...")
        fetcher = DataFetcher(exchange=args.exchange)
        try:
            ohlcv = fetcher.get_ohlcv(
                args.symbol,
                timeframe=args.timeframe,
                limit=args.limit
            )
            symbol = args.symbol
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("\nTip: Use --sample flag to test with sample data")
            sys.exit(1)

    print(f"Loaded {len(ohlcv)} bars")

    # Create engine
    engine = create_engine(preset=args.preset)

    # Run analysis
    if args.quick:
        print("\nQuick Scan Results:")
        result = engine.quick_scan(ohlcv, symbol=symbol)
        print(f"  Symbol: {result['symbol']}")
        print(f"  Price:  {result['price']:.2f}")
        print(f"  Regime: {result['regime']} (H={result['hurst']:.2f})")
        print(f"  Trend:  {result['trend']} (V={result['velocity']:.4f})")
        print(f"  Z-Score: {result['zscore']:.2f}")
        print(f"  Recommended: {result['recommendation']}")
    else:
        print("\nRunning full analysis...")
        conditions = engine.analyze(ohlcv, symbol=symbol)

        # Output results
        if args.format == 'text':
            print_summary(conditions)
        else:
            report = generate_report(conditions, output_format=args.format)
            print(report)

        # Create and save/show dashboard
        if args.output or args.show_chart:
            print("\nGenerating dashboard...")
            fig = create_dashboard(ohlcv, conditions, engine)

            if args.output:
                fig.write_html(args.output)
                print(f"Dashboard saved to: {args.output}")

            if args.show_chart:
                fig.show()


def run_demo():
    """Run a demonstration with sample data."""
    from quant_engine.core.engine import QuantEngine
    from quant_engine.data.fetcher import generate_sample_data
    from quant_engine.output.dashboard import print_summary

    print("=" * 60)
    print("  QUANT MARKET ANALYSIS ENGINE - DEMO")
    print("=" * 60)

    # Generate sample data with different characteristics
    print("\n1. Generating trending market sample...")
    trending_data = generate_sample_data(n_bars=500, volatility=0.015, trend=0.0005, seed=1)

    print("2. Generating choppy market sample...")
    choppy_data = generate_sample_data(n_bars=500, volatility=0.025, trend=0.0, seed=2)

    # Analyze both
    engine = QuantEngine()

    print("\n" + "=" * 60)
    print("  TRENDING MARKET ANALYSIS")
    print("=" * 60)
    trending_result = engine.analyze(trending_data, symbol="TRENDING_SAMPLE")
    print_summary(trending_result)

    print("\n" + "=" * 60)
    print("  CHOPPY MARKET ANALYSIS")
    print("=" * 60)
    choppy_result = engine.analyze(choppy_data, symbol="CHOPPY_SAMPLE")
    print_summary(choppy_result)

    print("\nDemo complete! Run with real data using:")
    print("  python -m quant_engine.main BTC/USDT --timeframe 1h")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # No arguments - run demo
        run_demo()
    else:
        main()
