from core.mt5_feed import MT5Feed
from core.config_loader import ConfigLoader

from trading_core.candles import CandleMetrics
from trading_core.volatility import Volatility

import MetaTrader5 as mt5


def run():
    print("Testing Volatility Module...")

    cfg = ConfigLoader().load_all()
    vcfg = cfg["strategies"]["volatility"]

    feed = MT5Feed()
    feed.initialize()
    df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 300)
    feed.shutdown()

    df = CandleMetrics.compute_basic(df)
    df = Volatility.compute_all(df, vcfg)

    print(df.tail(5)[["atr", "atr_percentile", "vol_expansion", "vol_compression"]])
    print("Volatility score:", Volatility.compute_volatility_score(df))


