#!/usr/bin/env python3
import csv, requests, time

PAIRS = ["BTCUSDT", "ETHUSDT", "LTCUSDT", "XRPUSDT"]
BIN_SIZE = {"BTCUSDT":10,"ETHUSDT":1,"LTCUSDT":0.1,"XRPUSDT":0.01}
OUTFILE = "agg_snapshot.csv"
BASE_URL = "https://data.binance.com/api/v3/depth"   # ← un-blocked host

def fetch_depth(symbol):
    r = requests.get(BASE_URL, params={"symbol":symbol,"limit":500}, timeout=5)
    r.raise_for_status()
    return r.json()

def bucket(depth, sym):
    size = BIN_SIZE[sym]
    bkt  = {}
    for side in ("bids","asks"):
        for p,q in depth[side]:
            price = round(float(p)/size)*size
            bkt.setdefault(price,[0,0])
            idx = 0 if side=="bids" else 1
            bkt[price][idx] += float(q)
    return bkt

rows=[["symbol","price","buy_qty","sell_qty"]]
for sym in PAIRS:
    for price,(buy,sell) in bucket(fetch_depth(sym),sym).items():
        rows.append([sym,price,round(buy,2),round(sell,2)])

with open(OUTFILE,"w",newline="") as f:
    csv.writer(f).writerows(rows)

print("✔ wrote", OUTFILE, "at", time.strftime("%H:%M:%S"), "UTC")
