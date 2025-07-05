#!/usr/bin/env python3
"""
Robust one-shot depth snapshot → agg_snapshot.csv
• Tries Binance mirror + Kraken REST
• Falls back to last CSV for any symbol that fails
• Never crashes, always writes a CSV (unless all fail)
"""

import csv, requests, time, os, sys

# ───────── CONFIG ──────────────────────────────────────────────────────────
PAIRS     = ["BTCUSDT", "ETHUSDT", "LTCUSDT", "XRPUSDT"]
BIN_SIZE  = {"BTCUSDT": 10, "ETHUSDT": 1, "LTCUSDT": 0.1, "XRPUSDT": 0.01}
OUTFILE   = "agg_snapshot.csv"
BINANCE_MIRROR = "https://data.binance.com/api/v3/depth"
KRAKEN_URL     = "https://api.kraken.com/0/public/Depth"
DEPTH_LIMIT    = 500
TIMEOUT        = 5
# ────────────────────────────────────────────────────────────────────────────

def load_old_snapshot():
    old = {}
    if os.path.exists(OUTFILE):
        with open(OUTFILE, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for sym, pr, b, s in reader:
                old.setdefault(sym, {})[float(pr)] = [float(b), float(s)]
    return old

def fetch_binance(sym):
    r = requests.get(BINANCE_MIRROR,
                     params={"symbol": sym, "limit": DEPTH_LIMIT},
                     timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def fetch_kraken(sym):
    base = sym[:-4]
    pair = "XBTUSD" if base == "BTC" else f"{base}USD"
    r = requests.get(KRAKEN_URL,
                     params={"pair": pair, "count": DEPTH_LIMIT},
                     timeout=TIMEOUT)
    r.raise_for_status()
    js = r.json().get("result", {})
    data = js.get(pair) or js.get(f"X{base}ZUSD")
    if data and "bids" in data:
        return {"bids": data["bids"], "asks": data["asks"]}
    return None

def get_orderbook(sym):
    for fn in (fetch_binance, fetch_kraken):
        try:
            ob = fn(sym)
            if ob and "bids" in ob and "asks" in ob:
                return ob
        except Exception:
            pass
    print(f"⚠️  Both APIs failed for {sym}", file=sys.stderr)
    return None

def bucketize(ob, sym):
    """Aggregate bids/asks into {bucket_price: [buyQty, sellQty]}."""
    # Determine bucket size (fallback if missing)
    size = BIN_SIZE.get(sym, max(0.001, float(ob["bids"][0][0]) * 0.002))
    buckets = {}
    for side in ("bids", "asks"):
        for entry in ob.get(side, []):
            # Safely grab the first two elements
            p = float(entry[0])
            q = float(entry[1])
            key = round(p / size) * size
            buy, sell = buckets.setdefault(key, [0.0, 0.0])
            if side == "bids":
                buckets[key][0] = buy + q
            else:
                buckets[key][1] = sell + q
    return buckets

def main():
    old_data = load_old_snapshot()
    rows     = [["symbol","price","buy_qty","sell_qty"]]
    any_success = False

    for sym in PAIRS:
        ob = get_orderbook(sym)
        if ob:
            buckets = bucketize(ob, sym)
            any_success = True
        else:
            buckets = old_data.get(sym, {})
            if buckets:
                print(f"ℹ️  Using last snapshot for {sym}", file=sys.stderr)
            else:
                print(f"❌ No data for {sym}, skipping", file=sys.stderr)

        for price in sorted(buckets):
            buy, sell = buckets[price]
            rows.append([sym, price, round(buy,2), round(sell,2)])

    if not any_success:
        print("❌ All symbols failed — no CSV written.", file=sys.stderr)
        sys.exit(1)

    with open(OUTFILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    print(f"✔ Wrote {OUTFILE} with {len(rows)-1} rows at",
          time.strftime("%Y-%m-%d %H:%M:%S"), "UTC")

if __name__ == "__main__":
    main()
