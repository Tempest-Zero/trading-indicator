# --- snapshot_once.py ----------------------------------
# Grab ONE depth snapshot from each exchange, bucket, write CSV, exit.
import json, asyncio, csv, websockets, math
PAIR = {"binance":"btcusdt","coinbase":"BTC-USD","kraken":"XBT/USD","bitfinex":"tBTCUSD"}
BIN  = 10
out  = "agg_snapshot.csv"
async def binance():
    url=f"wss://stream.binance.com:9443/ws/{PAIR['binance']}@depth20@100ms"
    async with websockets.connect(url) as ws:
        data=json.loads(await ws.recv())
        return [(float(p),float(q)) for p,q in data["bids"]],[(float(p),float(q)) for p,q in data["asks"]]
async def main():
    bids,asks=await binance()   # demo single exchange; expand like before
    buckets={}
    for p,q in bids: buckets.setdefault(math.floor(p/BIN)*BIN,[0,0])[0]+=q
    for p,q in asks:buckets.setdefault(math.floor(p/BIN)*BIN,[0,0])[1]+=q
    with open(out,"w",newline="") as f:
        w=csv.writer(f);w.writerow(["price","buy_qty","sell_qty"])
        for k in sorted(buckets):w.writerow([k,*buckets[k]])
asyncio.run(main())
