#!/usr/bin/env python3
"""
Quant Engine FastAPI Server

Usage:
    python -m quant_engine.api

Or with uvicorn directly:
    uvicorn quant_engine.api:app --reload --port 8000
"""

import sys
import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
    sys.exit(1)

from quant_engine.core.engine import QuantEngine
from quant_engine.data.fetcher import DataFetcher, generate_sample_data


# ============ PYDANTIC MODELS ============

class RegimeResponse(BaseModel):
    regime: str
    confidence: float
    hurst_value: float
    description: str


class TrendResponse(BaseModel):
    direction: str
    kalman_price: float
    velocity: float


class StatisticalResponse(BaseModel):
    zscore: float
    percentile: float
    condition: str


class VolumeResponse(BaseModel):
    delta_pct: float
    cumulative_trend: str


class KeyLevelsResponse(BaseModel):
    poc: float
    value_area_high: float
    value_area_low: float


class AnalysisResponse(BaseModel):
    symbol: str
    timestamp: str
    current_price: float
    regime: RegimeResponse
    trend: TrendResponse
    statistical: StatisticalResponse
    volume: VolumeResponse
    key_levels: KeyLevelsResponse
    pullback_probability: float
    continuation_probability: float
    suggested_bias: str
    confidence: float
    notes: List[str]


class OHLCVBar(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChartDataResponse(BaseModel):
    symbol: str
    timeframe: str
    ohlcv: List[OHLCVBar]
    kalman_line: List[float]
    hurst_series: List[float]
    zscore_series: List[float]
    volume_delta: List[float]


# ============ APP SETUP ============

app = FastAPI(
    title="Quant Market Analysis Engine",
    description="Market regime detection and statistical analysis API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
engine = QuantEngine()
fetcher = DataFetcher()


# ============ WEBSOCKET MANAGER ============

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = []

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()


# ============ HELPER FUNCTIONS ============

def get_regime_description(regime: str) -> str:
    descriptions = {
        "TRENDING": "Market showing persistent momentum. Trend-following strategies favored.",
        "MEAN_REVERTING": "Choppy market oscillating around mean. Fade extremes.",
        "RANDOM_WALK": "No statistical edge detected. Reduce position sizing.",
        "UNKNOWN": "Insufficient data for regime classification.",
    }
    return descriptions.get(regime, "")


def conditions_to_response(conditions) -> AnalysisResponse:
    return AnalysisResponse(
        symbol=conditions.symbol,
        timestamp=conditions.timestamp,
        current_price=conditions.current_price,
        regime=RegimeResponse(
            regime=conditions.regime,
            confidence=conditions.regime_confidence,
            hurst_value=conditions.hurst_value,
            description=get_regime_description(conditions.regime),
        ),
        trend=TrendResponse(
            direction=conditions.trend_direction,
            kalman_price=conditions.kalman_price,
            velocity=conditions.kalman_velocity,
        ),
        statistical=StatisticalResponse(
            zscore=conditions.zscore,
            percentile=conditions.percentile,
            condition=conditions.statistical_condition,
        ),
        volume=VolumeResponse(
            delta_pct=conditions.volume_delta_pct,
            cumulative_trend=conditions.cumulative_delta_trend,
        ),
        key_levels=KeyLevelsResponse(
            poc=conditions.poc,
            value_area_high=conditions.value_area_high,
            value_area_low=conditions.value_area_low,
        ),
        pullback_probability=conditions.pullback_probability,
        continuation_probability=conditions.trend_continuation_probability,
        suggested_bias=conditions.suggested_bias,
        confidence=conditions.confidence,
        notes=conditions.notes,
    )


# ============ REST ENDPOINTS ============

@app.get("/")
async def root():
    return {
        "name": "Quant Market Analysis Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze": "/api/v1/analyze/{symbol}",
            "chart_data": "/api/v1/chart-data/{symbol}",
            "symbols": "/api/v1/symbols",
            "demo": "/api/v1/demo",
        },
    }


@app.get("/api/v1/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_symbol(
    symbol: str,
    timeframe: str = Query("1h", regex="^(1m|5m|15m|1h|4h|1d)$"),
    limit: int = Query(500, ge=100, le=2000),
):
    """
    Full analysis for a symbol.

    Returns regime, trend, statistical position, volume analysis,
    key levels, and actionable probabilities.
    """
    try:
        ohlcv = fetcher.get_ohlcv(symbol, timeframe, limit)
        conditions = engine.analyze(ohlcv, symbol=symbol)
        return conditions_to_response(conditions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/demo", response_model=AnalysisResponse)
async def demo_analysis():
    """
    Run analysis on sample data (no API keys needed).
    """
    try:
        ohlcv = generate_sample_data(n_bars=500, seed=42)
        conditions = engine.analyze(ohlcv, symbol="DEMO")
        return conditions_to_response(conditions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chart-data/{symbol}", response_model=ChartDataResponse)
async def get_chart_data(
    symbol: str,
    timeframe: str = Query("1h", regex="^(1m|5m|15m|1h|4h|1d)$"),
    limit: int = Query(500, ge=100, le=2000),
):
    """
    Get OHLCV data with indicator overlays for charting.
    """
    try:
        ohlcv = fetcher.get_ohlcv(symbol, timeframe, limit)
        prices = ohlcv['close'].values

        from quant_engine.core.kalman import kalman_smooth
        from quant_engine.core.hurst import rolling_hurst
        from quant_engine.core.zscore import rolling_zscore
        from quant_engine.core.volume import volume_delta

        kalman = kalman_smooth(prices)
        hurst = rolling_hurst(prices, window=100)
        zscore = rolling_zscore(prices, window=20)
        vol_delta = volume_delta(ohlcv)

        ohlcv_bars = [
            OHLCVBar(
                timestamp=str(idx),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']),
            )
            for idx, row in ohlcv.iterrows()
        ]

        return ChartDataResponse(
            symbol=symbol,
            timeframe=timeframe,
            ohlcv=ohlcv_bars,
            kalman_line=[float(x) for x in kalman['filtered_price']],
            hurst_series=[float(x) if not (x != x) else 0.5 for x in hurst],  # Handle NaN
            zscore_series=[float(x) if not (x != x) else 0.0 for x in zscore['zscore']],
            volume_delta=[float(x) for x in vol_delta['delta']],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/symbols")
async def list_symbols():
    """List available symbols by category."""
    return {
        "crypto": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"],
        "stocks": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"],
        "indices": ["SPY", "QQQ", "DIA", "IWM"],
    }


@app.get("/api/v1/timeframes")
async def list_timeframes():
    """List supported timeframes."""
    return [
        {"value": "1m", "label": "1 Minute"},
        {"value": "5m", "label": "5 Minutes"},
        {"value": "15m", "label": "15 Minutes"},
        {"value": "1h", "label": "1 Hour"},
        {"value": "4h", "label": "4 Hours"},
        {"value": "1d", "label": "1 Day"},
    ]


# ============ WEBSOCKET ============

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time analysis updates.

    Client sends:
        {"action": "subscribe", "symbols": ["BTC/USDT", "ETH/USDT"]}
        {"action": "analyze", "symbol": "BTC/USDT"}
        {"action": "unsubscribe"}

    Server sends:
        {"type": "subscribed", "symbols": [...]}
        {"type": "analysis", "data": {...}}
        {"type": "error", "message": "..."}
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")

            if action == "subscribe":
                symbols = message.get("symbols", [])
                manager.subscriptions[client_id] = symbols
                await manager.send_message(client_id, {
                    "type": "subscribed",
                    "symbols": symbols,
                })

            elif action == "unsubscribe":
                manager.subscriptions[client_id] = []
                await manager.send_message(client_id, {"type": "unsubscribed"})

            elif action == "analyze":
                symbol = message.get("symbol")
                if symbol:
                    try:
                        ohlcv = fetcher.get_ohlcv(symbol, "1h", 500)
                        conditions = engine.analyze(ohlcv, symbol=symbol)
                        response = conditions_to_response(conditions)
                        await manager.send_message(client_id, {
                            "type": "analysis",
                            "data": response.dict(),
                        })
                    except Exception as e:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": str(e),
                        })

            elif action == "demo":
                try:
                    ohlcv = generate_sample_data(n_bars=500, seed=42)
                    conditions = engine.analyze(ohlcv, symbol="DEMO")
                    response = conditions_to_response(conditions)
                    await manager.send_message(client_id, {
                        "type": "analysis",
                        "data": response.dict(),
                    })
                except Exception as e:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": str(e),
                    })

    except WebSocketDisconnect:
        manager.disconnect(client_id)


# ============ MAIN ============

def main():
    import uvicorn
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           QUANT ENGINE API SERVER                         ║
    ╚═══════════════════════════════════════════════════════════╝

    Endpoints:
    • GET  /docs              - API documentation
    • GET  /api/v1/demo       - Demo analysis
    • GET  /api/v1/analyze/{symbol}
    • GET  /api/v1/chart-data/{symbol}
    • WS   /ws/{client_id}    - Real-time updates

    Starting server on http://localhost:8000
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
