
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
    async with websockets.connect(url, ping_interval=60):
        async for msg in websockets.WebSocketClientProtocol.recv_iter():
            d = json.loads(msg)
            bids = [(float(p), float(q)) for p, q in d["bids"]]
            asks = [(float(p), float(q)) for p, q in d["asks"]]
            await q.put(("binance", bids, asks))

async def coinbase_depth(pair, q):
    url = "wss://ws-feed.pro.coinbase.com"
    sub = {"type":"subscribe","product_ids":[pair],"channels":["level2"]}
    async with websockets.connect(url, ping_interval=60) as ws:
        await ws.send(json.dumps(sub))
        async for msg in ws:
            d = json.loads(msg)
            if d.get("type") in ("snapshot","l2update"):
                bids = [(float(p), float(q)) for p, q in d.get("bids",[])]
                asks = [(float(p), float(q)) for p, q in d.get("asks",[])]
                await q.put(("coinbase", bids, asks))

async def kraken_depth(pair, q):
    url = "wss://ws.kraken.com"
    sub = {"event":"subscribe","pair":[pair],"subscription":{"name":"book","depth":25}}
    async with websockets.connect(url, ping_interval=60) as ws:
        await ws.send(json.dumps(sub))
        async for msg in ws:
            if isinstance(msg, bytes): continue
            d = json.loads(msg)
            if isinstance(d, list) and len(d) > 1:
                book = d[1]
                bids = [(float(p), float(q)) for p, q in book.get("b",[])]
                asks = [(float(p), float(q)) for p, q in book.get("a",[])]
                await q.put(("kraken", bids, asks))

async def bitfinex_depth(pair, q):
    url = "wss://api-pub.bitfinex.com/ws/2"
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
                    await q.put(("bitfinex", bids, asks))

# Main aggregation loop ----------------------------------------------------
async def aggregator():
    q = asyncio.Queue()
    tasks = [binance_depth   (PAIRS["binance"] , q),
             coinbase_depth  (PAIRS["coinbase"], q),
             kraken_depth    (PAIRS["kraken"]  , q),
             bitfinex_depth  (PAIRS["bitfinex"], q)]
    tasks = [asyncio.create_task(t) for t in tasks]

    buy_hist, sell_hist = defaultdict(float), defaultdict(float)
    last_dump = 0

    while True:
        exch, bids, asks = await q.get()
        # weight by rough liquidity share (% of spot volume)
        weight = {"binance":0.5,"coinbase":0.2,"kraken":0.15,"bitfinex":0.15}[exch]
        for p, qy in bids:
            b = BIN_SIZE*round(p/BIN_SIZE)
            buy_hist[b] += qy*weight
        for p, qy in asks:
            b = BIN_SIZE*round(p/BIN_SIZE)
            sell_hist[b]+= qy*weight

        if time.time()-last_dump > DUMP_SEC:
            with open(OUTFILE,"w",newline="") as f:
                w=csv.writer(f); w.writerow(["price","buy_qty","sell_qty"])
                for b in sorted(set(buy_hist)|set(sell_hist)):
                    w.writerow([b, round(buy_hist[b],2), round(sell_hist[b],2)])
            print(f"⤴️  wrote {OUTFILE}  {time.strftime('%X')}")
            last_dump = time.time()

asyncio.run(aggregator())
# ──────────────────────────────────────────────────────────────────────────

