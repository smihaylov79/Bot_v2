# tests/test_candles.py

from trading_core.candles import CandleMetrics
from core.mt5_feed import MT5Feed
import MetaTrader5 as mt5

def run():
    print("Testing CandleMetrics...")

    feed = MT5Feed()
    feed.initialize()

    df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 100)
    feed.shutdown()

    df = CandleMetrics.compute_basic(df)
    df = CandleMetrics.add_atr(df)
    df = CandleMetrics.detect_impulse(df)

    print(df.tail())
