# tests/test_mt5_feed.py

from core.mt5_feed import MT5Feed
import MetaTrader5 as mt5

def run():
    print("Testing MT5Feed...")

    feed = MT5Feed()

    try:
        feed.initialize()
        print("MT5 initialized successfully.")
    except Exception as e:
        print(f"❌ MT5 initialization failed: {e}")
        return

    try:
        df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 10)
        print("Data fetched successfully:")
        print(df.tail())
    except Exception as e:
        print(f"❌ Failed to fetch OHLCV: {e}")

    feed.shutdown()
    print("MT5 shutdown OK.")
