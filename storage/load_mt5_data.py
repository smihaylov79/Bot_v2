import sys
from pathlib import Path
import yaml
import pandas as pd
import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.mt5_feed import MT5Feed
from storage.storage import MarketDataStorage


TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


def load_incremental(symbol, timeframe_str, timeframe_mt5, feed, db):
    print(f"\n=== {symbol} {timeframe_str} ===")

    last_ts = db.get_last_timestamp(symbol, timeframe_str)

    if last_ts is None:
        print("No data in DB → loading full history (10,000 candles)")
        df = feed.get_ohlcv(symbol, timeframe_mt5, 10000)
    else:
        print(f"Last timestamp in DB: {last_ts}")
        print("Fetching only new candles...")

        df = feed.get_ohlcv(symbol, timeframe_mt5, 2000)
        df = df[df["timestamp"] > last_ts]

        if df.empty:
            print("No new candles.")
            return

    print(f"Inserting {len(df)} candles...")
    db.insert_candles(symbol, timeframe_str, df)
    print("Done.")


def run():
    with open("config/general.yaml", "r") as f:
        general = yaml.safe_load(f)

    with open("config/symbols.yaml", "r") as f:
        symbols = yaml.safe_load(f)

    timeframes = general["timeframes"]

    feed = MT5Feed()
    feed.initialize()

    db = MarketDataStorage()

    for symbol, cfg in symbols.items():
        if not cfg.get("enabled", True):
            continue

        for tf in timeframes:
            load_incremental(symbol, tf, TIMEFRAME_MAP[tf], feed, db)

    feed.shutdown()
    print("\nAll data updated.")


if __name__ == "__main__":
    run()
