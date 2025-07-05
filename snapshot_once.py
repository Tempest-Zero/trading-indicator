#!/usr/bin/env python3
"""
Robust one-shot depth snapshot → agg_snapshot.csv
• Tries Binance data mirror + Kraken REST
• Falls back to last CSV for any symbol that fails
• Always writes a CSV unless *every* symbol fails
"""

import csv, requests, time, os, sys

# ───────── CONFIG ──────────────────────────────────────────────────────────
PAIRS     = ["BTCUSDT", "ETHUSDT", "LTCUSDT", "XRPUSDT"]  # your symbols
BIN_SIZE  = {                                            # per-symbol bucket
    "BTCUSDT": 10, "ETHUSDT": 1, "LTCUSDT": 0.1, "XRPUSDT": 0.01
}
OUTFILE   = "agg_snapshot.csv"
# Hosts to try, in order
BINANCE_MIRROR = "https://data.binance.com/api/v3/depth"
KRAKEN_URL     = "https://api.kraken.com/0/public/Depth"
DEPTH_LIMIT    = 500
TIMEOUT        = 5
# ────────────────────────────────────────────────────────────────────────────

def load_old_snapshot():
    """Load last CSV into { symbol: { price: [buy, sell], ... } }."""
    old = {}
    if os.path.exists(OUTFILE):
        with open(OUTFILE, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for sym,pr,b,s in reader:
                prf = float(pr); bf = float(b); sf = float(s)
                old.setdefault(sym, {})[prf] = [bf, sf]
    return old

def fetch_binance(sym):
    """Try Binance mirror."""
    r = requests.get(
        BINANCE_MIRROR,
        params={"symbol": sym, "limit": DEPTH_LIMIT},
        timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json()

def fetch_kraken(sym):
    """Try Kraken REST."""
    base = sym[:-4]  # "ETHUSDT" -> "ETH"
    pair = "XBTUSD" if base == "BTC" else f"{base}USD"
    r = requests.get(
        KRAKEN_URL,
        params={"pair": pair, "count": DEPTH_LIMIT},
        timeout=TIMEOUT
    )
    r.raise_for_status()
    j = r.json().get("result", {})
    data = j.get(pair) or j.get(f"X{base}ZUSD", None)
    if data and "bids" in data:
        return {"bids": data["bids"], "asks": data["asks"]}
    return None

def get_orderbook(sym):
    """Return orderbook dict or None."""
    try:
        return fetch_binance(sym)
    except Exception:
        pass
    try:
        return fetch_kraken(sym)
    except Exception:
        pass
    print(f"⚠️  Both APIs failed for {sym}", file=sys.stderr)
    return None

def bucketize(ob, sym):
    """Aggregate bids/asks into buckets {price: [buy, sell]}."""
    size = BIN_SIZE.get(sym, 
            max(0.001, float(ob["bids"][0][0]) * 0.002))
    buckets = {}
    for side in ("bids", "asks"):
        for p, q in ob[side]:
            price = float(p)
            bkey  = round(price / size) * size
            buy, sell = buckets.setdefault(bkey, [0.0, 0.0])
            if side == "bids":
                buckets[bkey][0] = buy + float(q)
            else:
                buckets[bkey][1] = sell + float(q)
    return buckets

def main():
    old_data = load_old_snapshot()
    rows     = [["symbol","price","buy_qty","sell_qty"]]
    success  = False

    for sym in PAIRS:
        ob = get_orderbook(sym)
        if ob:
            buckets = bucketize(ob, sym)
            success = True
        else:
            buckets = old_data.get(sym, {})
            if buckets:
                print(f"ℹ️  Using last snapshot for {sym}", file=sys.stderr)
            else:
                print(f"❌ No data for {sym}, skipping", file=sys.stderr)

        for pr in sorted(buckets):
            b, s = buckets[pr]
            rows.append([sym, pr, round(b,2), round(s,2)])

    if not success:
        print("❌ All symbols failed — no CSV written.", file=sys.stderr)
        sys.exit(1)

    with open(OUTFILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    print(f"✔ Wrote {OUTFILE} with {len(rows)-1} entries at",
          time.strftime("%Y-%m-%d %H:%M:%S"), "UTC")

if __name__ == "__main__":
    main()
