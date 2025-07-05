# snapshot_once.py — one-shot Kraken depth → CSV
import csv, requests, math

PAIR     = "XBTUSD"         # Kraken’s ticker for BTC/USD
BIN_SIZE = 10               # dollars per bucket
OUTFILE  = "agg_snapshot.csv"

# 1) fetch top 500 bids/asks from Kraken
url  = "https://api.kraken.com/0/public/Depth"
resp = requests.get(url, params={"pair": PAIR, "count": 500}, timeout=10)
resp.raise_for_status()
data = resp.json()["result"][PAIR]

# 2) bucket into price bins
buckets = {}  # price → [buyQty, sellQty]
for p, q in data["bids"]:
    price = float(p)
    b     = BIN_SIZE * round(price / BIN_SIZE)
    buckets.setdefault(b, [0, 0])[0] += float(q)
for p, q in data["asks"]:
    price = float(p)
    b     = BIN_SIZE * round(price / BIN_SIZE)
    buckets.setdefault(b, [0, 0])[1] += float(q)

# 3) write CSV
with open(OUTFILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["price", "buy_qty", "sell_qty"])
    for b in sorted(buckets):
        writer.writerow([b, *buckets[b]])

print("✔ wrote", OUTFILE)
