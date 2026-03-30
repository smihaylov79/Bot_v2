from core.mt5_feed import MT5Feed
from core.config_loader import ConfigLoader

from trading_core.candles import CandleMetrics
from trading_core.zones import Zones
from trading_core.trend import Trend

import MetaTrader5 as mt5


def run():
    print("Testing Trend Module...")

    cfg = ConfigLoader().load_all()
    tcfg = cfg["strategies"]["trend"]

    feed = MT5Feed()
    feed.initialize()
    df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 500)
    feed.shutdown()

    df = CandleMetrics.compute_basic(df)

    # swings for structure-based trend
    df = Zones.find_swings(df, left=3, right=3)

    df = Trend.compute_all(df, tcfg)

    print(df.tail(5)[["ma_fast", "ma_slow", "ma_trend_bull", "ma_trend_bear",
                      "swing_trend_bull", "swing_trend_bear"]])
    print("Trend score:", Trend.compute_trend_score(df))
    print(df.tail(1)[[
        "ma_trend_bull", "ma_trend_bear",
        "swing_trend_bull", "swing_trend_bear"
    ]])
