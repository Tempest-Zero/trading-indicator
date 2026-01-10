# Trading Indicator Project

This repository contains two main components:

1. **Order Book Snapshot Aggregator** - Real-time order book aggregation from multiple exchanges
2. **Quant Market Analysis Engine** - Sophisticated quantitative analysis framework

---

## Quant Market Analysis Engine

A professional-grade quantitative analysis framework that combines institutional-level indicators:

- **Hurst Exponent** - Regime detection (trending vs mean-reverting)
- **Kalman Filter** - Noise reduction with ~40% less lag than EMA
- **Z-Score** - Volatility-adaptive statistical triggers
- **Volume Analysis** - Buy/sell pressure and key levels

### Why This Works Better Than Retail Indicators

| Retail Approach | This Engine | Advantage |
|-----------------|-------------|-----------|
| RSI > 70 = Overbought | Z-Score > 2σ = Statistical anomaly | Adapts to volatility |
| EMA crossover (lagging) | Kalman Filter (predictive) | Reduces lag by ~40% |
| Same logic in all markets | Hurst Exponent regime detection | Avoids chop, saves capital |
| Fixed parameters | Dynamic, self-adjusting | Works across assets |

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with sample data (no API required)
python -m quant_engine.main --sample

# Analyze a crypto pair
python -m quant_engine.main BTC/USDT --timeframe 1h

# Analyze a stock
python -m quant_engine.main AAPL --timeframe 1d

# Generate interactive dashboard
python -m quant_engine.main BTC/USDT --show-chart
```

### Python API Usage

```python
from quant_engine import QuantEngine
from quant_engine.data import DataFetcher
from quant_engine.output import print_summary, create_dashboard

# Initialize
fetcher = DataFetcher()
engine = QuantEngine()

# Fetch data
ohlcv = fetcher.get_ohlcv('BTC/USDT', timeframe='1h', limit=500)

# Analyze
conditions = engine.analyze(ohlcv, symbol='BTC/USDT')

# Output
print_summary(conditions)

# Interactive chart
fig = create_dashboard(ohlcv, conditions, engine)
fig.show()
```

### Output Structure (MarketConditions)

```python
MarketConditions(
    symbol='BTC/USDT',
    timestamp='2024-01-15 10:00:00',

    # Regime Detection
    regime='TRENDING',           # TRENDING, MEAN_REVERTING, RANDOM_WALK
    regime_confidence=0.85,
    hurst_value=0.68,

    # Trend Analysis
    kalman_price=42150.50,
    kalman_velocity=0.0025,      # Positive = uptrend
    trend_direction='UP',

    # Statistical Position
    zscore=1.5,
    percentile=92,
    statistical_condition='HIGH',

    # Volume
    volume_delta_pct=15.2,
    cumulative_delta_trend='BULLISH',

    # Key Levels
    poc=42000.0,                 # Point of Control
    value_area_high=42500.0,
    value_area_low=41500.0,

    # Actionable Insights
    suggested_bias='UP',
    confidence=0.72,
    notes=['Trending regime favors momentum', ...]
)
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW OHLCV DATA INPUT                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: REGIME DETECTION (Hurst Exponent)                     │
│  ┌─────────────┬─────────────┬─────────────┐                    │
│  │ H < 0.5     │ H ≈ 0.5     │ H > 0.5     │                    │
│  │ Mean-Revert │ Random Walk │ Trending    │                    │
│  └─────────────┴─────────────┴─────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: NOISE FILTER (Kalman Filter)                          │
│  - Smooths price without traditional MA lag                     │
│  - Outputs: filtered_price, velocity, acceleration              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: STATISTICAL TRIGGER (Z-Score)                         │
│  - Standardized deviation from rolling mean                     │
│  - Dynamic thresholds based on current volatility               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: VALIDATION (Volume Analysis)                          │
│  - Volume Delta (buying vs selling pressure)                    │
│  - Volume Profile (POC, Value Area)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: MarketConditions Dashboard                             │
│  - Current regime + confidence                                  │
│  - Pullback/continuation probabilities                          │
│  - Suggested bias + key levels                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Module Reference

| Module | Description |
|--------|-------------|
| `quant_engine.core.hurst` | Hurst Exponent calculation (R/S and DFA methods) |
| `quant_engine.core.kalman` | Kalman Filter (with pykalman or pure numpy) |
| `quant_engine.core.zscore` | Z-Score with multi-timeframe confluence |
| `quant_engine.core.volume` | Volume delta, profile, VWAP, OBV |
| `quant_engine.core.engine` | Main QuantEngine integration class |
| `quant_engine.data.fetcher` | Data fetching (yfinance, ccxt) |
| `quant_engine.output.dashboard` | Plotly visualization |

### Presets

```python
from quant_engine.core.engine import create_engine

# Available presets
engine = create_engine('default')    # Balanced settings
engine = create_engine('fast')       # Lower latency, more noise
engine = create_engine('smooth')     # More stable, higher latency
engine = create_engine('aggressive') # Tighter thresholds
```

---

## Order Book Snapshot Aggregator

Connects to real-time WebSocket feeds from multiple cryptocurrency exchanges and aggregates the live BTC order book into fixed price bins.

### Supported Exchanges
- Binance (btcusdt)
- Coinbase (BTC-USD)
- Kraken (XBT/USD)
- Bitfinex (tBTCUSD)

### Usage

```bash
# Install websockets
pip install websockets

# Run snapshot
python snapshot_once.py
```

### Output Format (agg_snapshot.csv)

```csv
symbol,price,buy_qty,sell_qty
BTCUSDT,61000,4.32,5.21
BTCUSDT,61010,2.87,3.11
```

---

## Installation

```bash
# Full installation with all features
pip install -e ".[full]"

# Minimal (core analysis only)
pip install -e .

# With data fetching
pip install -e ".[data]"

# With visualization
pip install -e ".[viz]"
```

## Requirements

- Python 3.8+
- numpy, pandas, scipy (core)
- yfinance, ccxt (data fetching)
- plotly, matplotlib (visualization)
- pykalman (optional, pure numpy fallback available)

## License

MIT License
