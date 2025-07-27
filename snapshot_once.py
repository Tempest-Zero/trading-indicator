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
    try:
        r = requests.get(BINANCE_MIRROR,
                         params={"symbol": sym, "limit": DEPTH_LIMIT},
                         timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Binance API error for {sym}: {e}", file=sys.stderr)
        return None

def fetch_kraken(sym):
    # Better symbol mapping for Kraken
    symbol_map = {
        "BTCUSDT": "XBTUSD",
        "ETHUSDT": "ETHUSD", 
        "LTCUSDT": "LTCUSD",
        "XRPUSDT": "XRPUSD"
    }
    pair = symbol_map.get(sym, sym[:-4] + "USD")
    
    try:
        r = requests.get(KRAKEN_URL,
                         params={"pair": pair, "count": DEPTH_LIMIT},
                         timeout=TIMEOUT)
        r.raise_for_status()
        js = r.json().get("result", {})
        
        # Try multiple possible pair names that Kraken might return
        possible_pairs = [pair, f"X{pair}", pair.replace("USD", "ZUSD")]
        for p in possible_pairs:
            data = js.get(p)
            if data and "bids" in data and "asks" in data:
                return {"bids": data["bids"], "asks": data["asks"]}
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Kraken API error for {sym}: {e}", file=sys.stderr)
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
    # Determine bucket size with better fallback logic
    size = BIN_SIZE.get(sym)
    if not size:
        # Fallback: use 0.1% of current price as bucket size
        try:
            current_price = float(ob["bids"][0][0]) if ob["bids"] else float(ob["asks"][0][0])
            size = max(0.01, current_price * 0.001)  # At least 1 cent, max 0.1% of price
        except (IndexError, ValueError, TypeError):
            size = 1.0  # Default fallback
    
    buckets = {}
    for side in ("bids", "asks"):
        for entry in ob.get(side, []):
            try:
                # Safely grab the first two elements with validation
                p = float(entry[0])
                q = float(entry[1])
                
                # Validate data ranges
                if p <= 0 or q <= 0:
                    continue
                if p > 1000000 or q > 1000000:  # Reasonable limits
                    continue
                    
                key = round(p / size) * size
                buy, sell = buckets.setdefault(key, [0.0, 0.0])
                if side == "bids":
                    buckets[key][0] = buy + q
                else:
                    buckets[key][1] = sell + q
            except (ValueError, TypeError, IndexError):
                continue  # Skip invalid entries
    return buckets

def main():
    old_data = load_old_snapshot()
    rows     = [["symbol","price","buy_qty","sell_qty"]]
    any_success = False
    any_data = False  # Track if we have any data at all

    for sym in PAIRS:
        ob = get_orderbook(sym)
        if ob:
            buckets = bucketize(ob, sym)
            any_success = True
            any_data = True
        else:
            buckets = old_data.get(sym, {})
            if buckets:
                print(f"ℹ️  Using last snapshot for {sym}", file=sys.stderr)
                any_data = True
            else:
                print(f"❌ No data for {sym}, skipping", file=sys.stderr)

        for price in sorted(buckets):
            buy, sell = buckets[price]
            rows.append([sym, price, round(buy,2), round(sell,2)])

    if not any_data:
        print("❌ No data available — no CSV written.", file=sys.stderr)
        sys.exit(1)

    with open(OUTFILE, "w", newline="") as f:
        csv.writer(f).writerows(rows)

    status_msg = "✔ Updated" if any_success else "✔ Reused existing data for"
    print(f"{status_msg} {OUTFILE} with {len(rows)-1} rows at",
          time.strftime("%Y-%m-%d %H:%M:%S"), "UTC")

if __name__ == "__main__":
    main()
