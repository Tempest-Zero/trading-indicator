#!/usr/bin/env python3
"""
Quant Market Analysis Engine - CLI

Usage:
    python -m quant_engine.main              # Interactive mode
    python -m quant_engine.main BTC/USDT     # Analyze crypto
    python -m quant_engine.main AAPL         # Analyze stock
    python -m quant_engine.main --demo       # Run with sample data
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print app banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║           QUANT MARKET ANALYSIS ENGINE                    ║
    ║                                                           ║
    ║   Hurst | Kalman | Z-Score | Volume                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_result(result):
    """Print analysis result in a clean format."""

    # Determine colors/symbols based on values
    regime_icon = {"TRENDING": "📈", "MEAN_REVERTING": "🔄", "RANDOM_WALK": "❓", "UNKNOWN": "❓"}
    trend_icon = {"UP": "▲", "DOWN": "▼", "NEUTRAL": "◆"}
    bias_icon = {"UP": "🟢", "DOWN": "🔴", "NEUTRAL": "⚪", "WAIT": "🟡"}

    regime = result.regime
    trend = result.trend_direction
    bias = result.suggested_bias

    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  {result.symbol:^55}  │
    │  {result.timestamp[:19]:^55}  │
    └─────────────────────────────────────────────────────────────┘

    MARKET REGIME                          CURRENT PRICE
    {regime_icon.get(regime, '?')} {regime:<20}              ${result.current_price:,.2f}
       Hurst: {result.hurst_value:.3f}
       Confidence: {result.regime_confidence:.0%}

    ┌────────────────────────────────────────┐
    │  TREND: {trend_icon.get(trend, '?')} {trend:<10}                     │
    │  Kalman Price: ${result.kalman_price:,.2f}              │
    │  Velocity: {result.kalman_velocity:+.4f}                     │
    └────────────────────────────────────────┘

    STATISTICAL POSITION
    ├─ Z-Score:    {result.zscore:+.2f}  {'← OVERSOLD' if result.zscore < -2 else '← OVERBOUGHT' if result.zscore > 2 else ''}
    ├─ Percentile: {result.percentile:.0f}%
    └─ Condition:  {result.statistical_condition}

    VOLUME ANALYSIS
    ├─ Delta:      {result.volume_delta_pct:+.1f}%
    ├─ Pressure:   {result.cumulative_delta_trend}
    └─ Rel Volume: {result.relative_volume:.2f}x

    KEY LEVELS
    ├─ Value High: ${result.value_area_high:,.2f}
    ├─ POC:        ${result.poc:,.2f}
    └─ Value Low:  ${result.value_area_low:,.2f}

    ╔═══════════════════════════════════════════════════════════════╗
    ║  SIGNAL: {bias_icon.get(bias, '?')} {bias:<10}  CONFIDENCE: {result.confidence:.0%}               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  Pullback Prob:     {result.pullback_probability:.0%}                                 ║
    ║  Continuation Prob: {result.trend_continuation_probability:.0%}                                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Print notes
    if result.notes:
        print("    ANALYSIS NOTES:")
        for note in result.notes:
            print(f"    • {note}")
        print()


def run_analysis(symbol, timeframe='1h', limit=500, use_sample=False):
    """Run analysis on a symbol."""
    from quant_engine.core.engine import QuantEngine
    from quant_engine.data.fetcher import DataFetcher, generate_sample_data

    print(f"\n    Loading data{'...' if use_sample else f' for {symbol}...'}")

    if use_sample:
        ohlcv = generate_sample_data(n_bars=limit, seed=42)
        symbol = "SAMPLE_DATA"
    else:
        try:
            fetcher = DataFetcher()
            ohlcv = fetcher.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except ImportError as e:
            print(f"\n    Error: Missing dependency - {e}")
            print("    Install with: pip install yfinance ccxt")
            return None
        except Exception as e:
            print(f"\n    Error fetching data: {e}")
            return None

    print(f"    Loaded {len(ohlcv)} bars")
    print("    Running analysis...")

    engine = QuantEngine()
    result = engine.analyze(ohlcv, symbol=symbol)

    return result


def interactive_mode():
    """Run interactive CLI mode."""
    clear_screen()
    print_banner()

    print("""
    COMMANDS:
    ─────────────────────────────────────────
    [1] Analyze crypto pair (e.g., BTC/USDT)
    [2] Analyze stock (e.g., AAPL)
    [3] Run demo with sample data
    [4] Quick multi-asset scan
    [q] Quit
    ─────────────────────────────────────────
    """)

    while True:
        choice = input("    Enter choice: ").strip().lower()

        if choice == 'q':
            print("\n    Goodbye!\n")
            break

        elif choice == '1':
            symbol = input("    Enter crypto pair (e.g., BTC/USDT): ").strip().upper()
            if symbol:
                result = run_analysis(symbol)
                if result:
                    print_result(result)

        elif choice == '2':
            symbol = input("    Enter stock ticker (e.g., AAPL): ").strip().upper()
            if symbol:
                result = run_analysis(symbol)
                if result:
                    print_result(result)

        elif choice == '3':
            result = run_analysis("DEMO", use_sample=True)
            if result:
                print_result(result)

        elif choice == '4':
            print("\n    Quick scan not yet implemented in interactive mode.")
            print("    Use: python -m quant_engine.main SYMBOL1 SYMBOL2 ...\n")

        else:
            print("    Invalid choice. Try again.\n")

        print("\n    ─────────────────────────────────────────")
        print("    [1] Crypto  [2] Stock  [3] Demo  [q] Quit")
        print("    ─────────────────────────────────────────\n")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # No args = interactive mode
    if not args:
        interactive_mode()
        return

    # Help
    if args[0] in ['-h', '--help']:
        print("""
Quant Market Analysis Engine

Usage:
    python -m quant_engine.main                  Interactive mode
    python -m quant_engine.main BTC/USDT         Analyze crypto
    python -m quant_engine.main AAPL             Analyze stock
    python -m quant_engine.main --demo           Demo with sample data
    python -m quant_engine.main -t 4h BTC/USDT   Custom timeframe

Options:
    -t, --timeframe   Candle timeframe (1m,5m,15m,1h,4h,1d) [default: 1h]
    -n, --bars        Number of bars to analyze [default: 500]
    --demo            Use sample data (no API needed)
    --json            Output as JSON
        """)
        return

    # Parse simple args
    timeframe = '1h'
    limit = 500
    use_sample = False
    output_json = False
    symbols = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ['-t', '--timeframe'] and i + 1 < len(args):
            timeframe = args[i + 1]
            i += 2
        elif arg in ['-n', '--bars'] and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif arg == '--demo':
            use_sample = True
            i += 1
        elif arg == '--json':
            output_json = True
            i += 1
        elif not arg.startswith('-'):
            symbols.append(arg)
            i += 1
        else:
            i += 1

    # Run analysis
    print_banner()

    if use_sample or not symbols:
        result = run_analysis("DEMO", timeframe=timeframe, limit=limit, use_sample=True)
        if result:
            if output_json:
                import json
                print(json.dumps(result.to_dict(), indent=2, default=str))
            else:
                print_result(result)
    else:
        for symbol in symbols:
            result = run_analysis(symbol, timeframe=timeframe, limit=limit)
            if result:
                if output_json:
                    import json
                    print(json.dumps(result.to_dict(), indent=2, default=str))
                else:
                    print_result(result)


if __name__ == '__main__':
    main()
