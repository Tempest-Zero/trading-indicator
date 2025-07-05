

import csv, requests, time, sys

# ────────── USER CONFIG ────────────────────────────────────────────────────
PAIRS = ["BTCUSDT", "ETHUSDT", "LTCUSDT", "XRPUSDT"]      # add more symbols here
BIN_SIZE = {                                              # per-symbol bucket size
    "BTCUSDT": 10,
    "ETHUSDT": 1,
    "LTCUSDT": 0.1,
    "XRPUSDT": 0.01,
}
OUTFILE = "agg_snapshot.csv"
HOSTS   = [   # try in this order until one responds with valid JSON
    "https://data.binance.com/api/v3/depth",
    "https://api1.binance.com/api/v3/depth",
    "https://api2.binance.com/api/v3/depth",
    "https://api3.binance.com/api/v3/depth",
]
DEPTH_LIMIT = 500
TIMEOUT_SEC = 5
# ───────────────────────────────────────────────────────────────────────────

def fetch_depth(symbol: str) -> dict | None:
    """Return JSON with bids/asks or None if all hosts fail."""
    for base in HOSTS:
        try:
            r = requests.get(
                base,
                params={"symbol": symbol, "limit": DEPTH_LIMIT},
                timeout=TIMEOUT_SEC,
            )
            if r.status_code != 200:
                continue               # try next host
            data = r.json()
            if "bids" in data and "asks" in data:
                return data
        except Exception:
            continue                   # JSON error or network error → try next host
    print(f"⚠️  All hosts failed for {symbol}", file=sys.stderr)
    return None

def bucketize(orderbook: dict, symbol: str) -> dict[float, list[float, float]]:
    """Aggregate into price buckets."""
    size = BIN_SIZE.get(symbol, max(0.001, float(orderbook["bids"][0][0]) * 0.002))
    buckets: dict[float, list[float, float]] = {}
    for side in ("bids", "asks"):
        for price, qty in orderbook[side]:
            p = float(price)
            b = round(p / size) * size
            buy, sell = buckets.setdefault(b, [0.0, 0.0])
            if side == "bids":
                buckets[b][0] = buy + float(qty)
            else:
                buckets[b][1] = sell + float(qty)
    return buckets

def main() -> None:
    rows = [["symbol", "price", "buy_qty", "sell_qty"]]
    for sym in PAIRS:
        ob = fetch_depth(sym)
        if not ob:
            continue                           # skip symbol on failure
        for price, (buy, sell) in bucketize(ob, sym).items():
            rows.append([sym, price, round(buy, 2), round(sell, 2)])

    if len(rows) == 1:
        print("❌ Snapshot failed for all symbols.")
        sys.exit(1)

    with open(OUTFILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    print(f"✔ Wrote {OUTFILE} with {len(rows)-1} rows at",
          time.strftime("%Y-%m-%d %H:%M:%S"), "UTC")

if __name__ == "__main__":
    main()
