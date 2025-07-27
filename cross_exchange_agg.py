
import asyncio, json, time, csv, math, websockets
from collections import defaultdict

# CONFIG – add/remove exchanges or change BIN_SIZE here

PAIRS      = {"binance":  "btcusdt",
              "coinbase": "BTC-USD",
              "kraken":   "XBT/USD",
              "bitfinex": "tBTCUSD"}
BIN_SIZE   = 10          # dollars per bucket
DUMP_SEC   = 30          # write file every N seconds
OUTFILE    = "agg_snapshot.csv"
# Exchange-specific helpers ------------------------------------------------
async def binance_depth(pair, q):
    url = f"wss://stream.binance.com:9443/ws/{pair}@depth20@100ms"
    while True:
        try:
            async with websockets.connect(url, ping_interval=60) as ws:
                async for msg in ws:
                    d = json.loads(msg)
                    if "bids" in d and "asks" in d:
                        bids = [(float(p), float(q)) for p, q in d["bids"]]
                        asks = [(float(p), float(q)) for p, q in d["asks"]]
                        await q.put(("binance", bids, asks))
        except Exception as e:
            print(f"Binance connection error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)

async def coinbase_depth(pair, q):
    url = "wss://ws-feed.pro.coinbase.com"
    sub = {"type":"subscribe","product_ids":[pair],"channels":["level2"]}
    while True:
        try:
            async with websockets.connect(url, ping_interval=60) as ws:
                await ws.send(json.dumps(sub))
                async for msg in ws:
                    d = json.loads(msg)
                    if d.get("type") in ("snapshot","l2update"):
                        bids = [(float(p), float(q)) for p, q in d.get("bids",[])]
                        asks = [(float(p), float(q)) for p, q in d.get("asks",[])]
                        if bids or asks:  # Only send if we have data
                            await q.put(("coinbase", bids, asks))
        except Exception as e:
            print(f"Coinbase connection error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)

async def kraken_depth(pair, q):
    url = "wss://ws.kraken.com"
    sub = {"event":"subscribe","pair":[pair],"subscription":{"name":"book","depth":25}}
    while True:
        try:
            async with websockets.connect(url, ping_interval=60) as ws:
                await ws.send(json.dumps(sub))
                async for msg in ws:
                    if isinstance(msg, bytes): continue
                    d = json.loads(msg)
                    if isinstance(d, list) and len(d) > 1:
                        book = d[1]
                        if isinstance(book, dict):
                            bids = [(float(p), float(q)) for p, q in book.get("b",[])]
                            asks = [(float(p), float(q)) for p, q in book.get("a",[])]
                            if bids or asks:  # Only send if we have data
                                await q.put(("kraken", bids, asks))
        except Exception as e:
            print(f"Kraken connection error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)

async def bitfinex_depth(pair, q):
    url = "wss://api-pub.bitfinex.com/ws/2"
    while True:
        try:
            async with websockets.connect(url, ping_interval=60) as ws:
                await ws.send(json.dumps({"event":"conf","flags":131072}))
                await ws.send(json.dumps({"event":"subscribe","channel":"book","symbol":pair,"len":25}))
                chan_id = None
                async for raw in ws:
                    d = json.loads(raw)
                    if isinstance(d, dict) and d.get("event")=="subscribed":
                        chan_id = d["chanId"]; continue
                    if isinstance(d, list) and d[0]==chan_id:
                        data = d[1]
                        if isinstance(data, list) and data and isinstance(data[0], list):
                            bids = [(abs(p), q) for p, q, _ in data if q > 0]
                            asks = [(p, abs(q)) for p, q, _ in data if q < 0]
                            if bids or asks:  # Only send if we have data
                                await q.put(("bitfinex", bids, asks))
        except Exception as e:
            print(f"Bitfinex connection error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)

# Main aggregation loop ----------------------------------------------------
async def aggregator():
    q = asyncio.Queue()
    tasks = [binance_depth   (PAIRS["binance"] , q),
             coinbase_depth  (PAIRS["coinbase"], q),
             kraken_depth    (PAIRS["kraken"]  , q),
             bitfinex_depth  (PAIRS["bitfinex"], q)]
    tasks = [asyncio.create_task(t) for t in tasks]

    buy_hist, sell_hist = defaultdict(float), defaultdict(float)
    data_timestamps = defaultdict(float)  # Track when data was last updated
    last_dump = 0
    DATA_EXPIRE_SEC = 300  # Expire data after 5 minutes

    while True:
        exch, bids, asks = await q.get()
        current_time = time.time()
        
        # Clear expired data every dump cycle
        if current_time - last_dump > DUMP_SEC:
            expired_buckets = [b for b, ts in data_timestamps.items() 
                             if current_time - ts > DATA_EXPIRE_SEC]
            for bucket in expired_buckets:
                buy_hist.pop(bucket, None)
                sell_hist.pop(bucket, None)
                data_timestamps.pop(bucket, None)
        
        # weight by rough liquidity share (% of spot volume)
        weight = {"binance":0.5,"coinbase":0.2,"kraken":0.15,"bitfinex":0.15}[exch]
        for p, qy in bids:
            if p > 0 and qy > 0:  # Validate data
                b = BIN_SIZE*round(p/BIN_SIZE)
                buy_hist[b] = qy*weight  # Replace instead of accumulate
                data_timestamps[b] = current_time
        for p, qy in asks:
            if p > 0 and qy > 0:  # Validate data
                b = BIN_SIZE*round(p/BIN_SIZE)
                sell_hist[b] = qy*weight  # Replace instead of accumulate
                data_timestamps[b] = current_time

        if time.time()-last_dump > DUMP_SEC:
            with open(OUTFILE,"w",newline="") as f:
                w=csv.writer(f); w.writerow(["symbol","price","buy_qty","sell_qty"])
                for b in sorted(set(buy_hist)|set(sell_hist)):
                    w.writerow(["BTCUSDT", b, round(buy_hist[b],2), round(sell_hist[b],2)])
            print(f"⤴️  wrote {OUTFILE}  {time.strftime('%X')}")
            last_dump = time.time()

asyncio.run(aggregator())
# ──────────────────────────────────────────────────────────────────────────

