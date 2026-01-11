# Quant Market Analysis Engine

A professional-grade quantitative analysis framework combining institutional-level indicators:

- **Hurst Exponent** - Regime detection (trending vs mean-reverting)
- **Kalman Filter** - Noise reduction with ~40% less lag than EMA
- **Z-Score** - Volatility-adaptive statistical triggers
- **Volume Analysis** - Buy/sell pressure and key levels

## Why This Works Better Than Retail Indicators

| Retail Approach | This Engine | Advantage |
|-----------------|-------------|-----------|
| RSI > 70 = Overbought | Z-Score > 2σ = Statistical anomaly | Adapts to volatility |
| EMA crossover (lagging) | Kalman Filter (predictive) | Reduces lag by ~40% |
| Same logic in all markets | Hurst Exponent regime detection | Avoids chop, saves capital |
| Fixed parameters | Dynamic, self-adjusting | Works across assets |

## Quick Start

```bash
# Install dependencies
pip install numpy pandas scipy

# Run interactive CLI
python -m quant_engine.main

# Run with demo data (no API needed)
python -m quant_engine.main --demo

# Analyze a specific symbol (requires yfinance or ccxt)
pip install yfinance ccxt
python -m quant_engine.main BTC/USDT
python -m quant_engine.main AAPL
```

## CLI Usage

```bash
# Interactive mode (menu-driven)
python -m quant_engine.main

# Direct analysis
python -m quant_engine.main BTC/USDT           # Crypto
python -m quant_engine.main AAPL               # Stock
python -m quant_engine.main --demo             # Sample data

# Options
python -m quant_engine.main -t 4h BTC/USDT     # Custom timeframe
python -m quant_engine.main -n 1000 AAPL       # More bars
python -m quant_engine.main --json BTC/USDT    # JSON output
```

## Python API

```python
from quant_engine.core.engine import QuantEngine
from quant_engine.data.fetcher import generate_sample_data

# Create engine
engine = QuantEngine()

# Use sample data (no API needed)
ohlcv = generate_sample_data(n_bars=500)

# Analyze
result = engine.analyze(ohlcv, symbol='TEST')

# Access results
print(f"Regime: {result.regime} ({result.regime_confidence:.0%})")
print(f"Trend: {result.trend_direction}")
print(f"Z-Score: {result.zscore:.2f}")
print(f"Bias: {result.suggested_bias} ({result.confidence:.0%})")
```

## Output Example

```
╔═══════════════════════════════════════════════════════════════╗
║  SIGNAL: 🟢 UP        CONFIDENCE: 72%                        ║
╠═══════════════════════════════════════════════════════════════╣
║  Pullback Prob:     35%                                       ║
║  Continuation Prob: 65%                                       ║
╚═══════════════════════════════════════════════════════════════╝

ANALYSIS NOTES:
• Trending regime (H=82%) favors momentum
• Volume delta confirms uptrend
• Price above Kalman filter
```

## Architecture

```
RAW OHLCV DATA
      │
      ▼
┌─────────────────────────────────────┐
│  LAYER 1: REGIME (Hurst Exponent)   │
│  H < 0.5 = Mean Revert              │
│  H > 0.5 = Trending                 │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  LAYER 2: FILTER (Kalman)           │
│  Smoothed price + velocity          │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  LAYER 3: STATS (Z-Score)           │
│  Statistical position               │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  LAYER 4: VOLUME                    │
│  Buy/sell pressure + key levels     │
└─────────────────────────────────────┘
      │
      ▼
   SIGNAL + CONFIDENCE
```

## Web API (FastAPI)

Start the API server:

```bash
pip install fastapi uvicorn
python -m quant_engine.api
```

Endpoints:
- `GET /api/v1/analyze/{symbol}` - Full analysis
- `GET /api/v1/chart-data/{symbol}` - OHLCV + indicators
- `GET /api/v1/symbols` - Available symbols
- `WS /ws/{client_id}` - Real-time updates

## Web Frontend (Next.js)

A modern React dashboard with real-time updates.

### Features

- Professional candlestick charts with TradingView Lightweight Charts
- Kalman filter overlay on price chart
- Regime card with Hurst value and gauge
- Z-Score indicator with colored histogram
- Volume delta chart
- Action panel with bias and probabilities
- Key levels (POC, Value Area)
- Trend card with velocity
- Symbol selector with search
- Timeframe selector (1m, 5m, 15m, 1H, 4H, 1D)
- Watchlist sidebar with live updates
- Real-time WebSocket updates
- Connection status indicator
- Dark mode UI

### Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Then open http://localhost:3000 in your browser.

### Stack

- **Next.js 14** - React framework with App Router
- **TailwindCSS** - Utility-first styling
- **TanStack Query** - Data fetching with caching
- **Zustand** - State management
- **Lightweight Charts** - Professional charting
- **Lucide React** - Icons

### Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Requirements

- Python 3.8+
- numpy, pandas, scipy (core)
- yfinance (stocks) or ccxt (crypto) for live data
- fastapi, uvicorn (web API)

## Installation

```bash
# Core only
pip install numpy pandas scipy

# With data fetching
pip install numpy pandas scipy yfinance ccxt

# With web API
pip install numpy pandas scipy fastapi uvicorn

# Everything
pip install -e ".[full]"
```

## License

MIT License
