# snapshot_once.py  – one-shot REST depth -> CSV
# ------------------------------------------------
import csv, requests, math

PAIR      = "BTCUSDT"
BIN_SIZE  = 10             # dollars per bucket
OUTFILE   = "agg_snapshot.csv"

# 1) grab top 1000 bids/asks (free, no key needed)
url  = "https://api.binance.com/api/v3/depth"
resp = requests.get(url, params={"symbol": PAIR, "limit": 1000}, timeout=10)
resp.raise_for_status()
data = resp.json()

# 2) bucket
buckets = {}                       # price bucket -> [buyQty, sellQty]
for p, q in data["bids"]:
    b = BIN_SIZE * round(float(p) / BIN_SIZE)
    buckets.setdefault(b, [0, 0])[0] += float(q)

for p, q in data["asks"]:
    b = BIN_SIZE * round(float(p) / BIN_SIZE)
    buckets.setdefault(b, [0, 0])[1] += float(q)

# 3) write csv
with open(OUTFILE, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["price", "buy_qty", "sell_qty"])
    for b in sorted(buckets):
        w.writerow([b, *buckets[b]])

print("✔ wrote", OUTFILE)
