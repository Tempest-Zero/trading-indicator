#!/usr/bin/env python3
# snapshot_once.py  —  One-shot REST depth snapshot → agg_snapshot.csv

import csv
import time
import math
import requests

# ── USER CONFIG ────────────────────────────────────────────────────────────
PAIRS = [
    "BTCUSDT",
    "ETHUSDT",
    "LTCUSDT",
    "XRPUSDT",
    # add more symbols here as needed
]
# Optimal bucket sizes per symbol (in quote-currency units)
BIN_SIZE = {
    "BTCUSDT": 10,
    "ETHUSDT": 1,
    "LTCUSDT": 0.1,
    "XRPUSDT": 0.01,
}
OUTFILE = "agg_snapshot.csv"   # CSV written to repo root
# ──────────────────────────────────────────────────────────────────────────

def fetch_depth(symbol: str) -> dict:
    """Fetch top 500 levels from Binance REST order-book."""
    url = "https://api.binance.com/api/v3/depth"
    resp = requests.get(url, params={"symbol": symbol, "limit": 500}, timeout=5)
    resp.raise_for_status()
    return resp.json()

def bucketize(depth: dict, symbol: str) -> dict:
    """Turn raw bids/asks into {bucket_price: [buyQty, sellQty]}."""
    size = BIN_SIZE.get(symbol, BIN_SIZE[PAIRS[0]])
    buckets: dict[float, list[float, float]] = {}
    for side in ("bids", "asks"):
        for price_str, qty_str in depth[side]:
            p = float(price_str)
            b = round(p / size) * size
            buy, sell = buckets.setdefault(b, [0.0, 0.0])
            if side == "bids":
                buckets[b][0] = buy + float(qty_str)
            else:
                buckets[b][1] = sell + float(qty_str)
    return buckets

def main():
    rows = [["symbol", "price", "buy_qty", "sell_qty"]]
    for sym in PAIRS:
        data    = fetch_depth(sym)
        buckets = bucketize(data, sym)
        for price in sorted(buckets):
            buy_qty, sell_qty = buckets[price]
            rows.append([sym, price, round(buy_qty, 2), round(sell_qty, 2)])

    with open(OUTFILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"✔ Wrote {OUTFILE} at {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

if __name__ == "__main__":
    main()
