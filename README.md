Order Book Snapshot Aggregator
This project connects to real-time WebSocket feeds from multiple cryptocurrency exchanges — Binance, Coinbase, Kraken, and Bitfinex — and aggregates the live BTC order book into fixed price bins. The system weights each exchange’s liquidity and outputs a consolidated snapshot in CSV format, updating every 30 seconds.

Additionally, the repository includes a GitHub Actions workflow (snapshot-once) that allows automated snapshots on a schedule (e.g., every 5 minutes) and commits the output to the repo.

What This Does
Streams live order book data from:

Binance (btcusdt)

Coinbase (BTC-USD)

Kraken (XBT/USD)

Bitfinex (tBTCUSD)

Aggregates bids and asks into price buckets of configurable size (default: $10).

Applies weightings per exchange (to reflect estimated liquidity share).

Outputs a CSV file (agg_snapshot.csv) with total buy and sell quantities per bucket.

GitHub Actions workflow runs the script and commits fresh CSV snapshots on a schedule.

Output Format (agg_snapshot.csv)
The snapshot file contains three columns:

python-repl
Copy
Edit
price,buy_qty,sell_qty
61000,4.32,5.21
61010,2.87,3.11
...
Each row shows the total weighted quantity of buy and sell orders for that price level (rounded to nearest bucket size).

How to Run Locally
Install dependencies:

bash
Copy
Edit
pip install websockets
Run the script:

bash
Copy
Edit
python snapshot_once.py
This will begin streaming and aggregating order book data in real time. A new CSV file will be written every 30 seconds.

GitHub Actions: Scheduled Snapshots
The workflow file snapshot-once.yml enables automatic snapshot generation and commit via GitHub Actions.

Schedule
Runs every 5 minutes (*/5 * * * *)

You can also trigger it manually via the "Run workflow" button on GitHub.

What It Does
Checks out the repo

Runs snapshot_once.py

If the agg_snapshot.csv file has changed, commits the updated snapshot back to the main branch

Customization Options
You can modify the following parameters inside the script:

python
Copy
Edit
PAIRS = {
    "binance":  "btcusdt",
    "coinbase": "BTC-USD",
    "kraken":   "XBT/USD",
    "bitfinex": "tBTCUSD"
}

BIN_SIZE = 10         # price bucket size in USD
DUMP_SEC = 30         # interval to write CSV file
OUTFILE  = "agg_snapshot.csv"
Adjust BIN_SIZE or DUMP_SEC based on how granular or frequent you want the snapshots to be.

Notes
The script uses asynchronous WebSocket connections and a queue to collect and aggregate order book messages.

Each exchange has its own message format and subscription mechanism, which is handled in a separate helper function.

WebSocket ping intervals are set to prevent disconnections.
