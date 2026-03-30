# tests/test_patterns.py

from core.mt5_feed import MT5Feed
from trading_core.candles import CandleMetrics
from trading_core.patterns import Patterns
import MetaTrader5 as mt5

def run():
    print("Testing Patterns...")

    feed = MT5Feed()
    feed.initialize()
    df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 200)
    feed.shutdown()

    df = CandleMetrics.compute_basic(df)
    df = Patterns.detect_all(df)

    print(df.tail())

