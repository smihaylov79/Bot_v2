# tests/test_confluence.py
from analysis.signals import SignalGenerator
from core.mt5_feed import MT5Feed
from core.config_loader import ConfigLoader

from analysis.candles import CandleMetrics
from analysis.patterns import Patterns
from analysis.zones import Zones
from analysis.confluence import ConfluenceEngine

import MetaTrader5 as mt5

from core.strategy_engine import StrategyEngine


def run():
    print("Testing Confluence Engine...")

    # Load config
    cfg = ConfigLoader().load_all()
    symbol_cfg = cfg["symbols"]["EURUSD"]["patterns"]
    zone_cfg = cfg["strategies"]["zones"]
    strategy_cfg = cfg["strategies"]["strategy"]

    # Fetch data
    feed = MT5Feed()
    feed.initialize()
    df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 300)
    feed.shutdown()

    # Candle metrics
    df = CandleMetrics.compute_basic(df)
    df = CandleMetrics.add_atr(df)

    # Patterns
    df = Patterns.detect_all(df)

    # Zones (micro + macro)
    df_micro = Zones.find_swings(df,
                                 left=zone_cfg["micro"]["left"],
                                 right=zone_cfg["micro"]["right"])
    df_macro = Zones.find_swings(df,
                                 left=zone_cfg["macro"]["left"],
                                 right=zone_cfg["macro"]["right"])

    zones_micro = Zones.cluster_zones(df_micro, tolerance=zone_cfg["tolerance"])
    zones_macro = Zones.cluster_zones(df_macro, tolerance=zone_cfg["tolerance"])

    # Combine zones
    all_zones = zones_micro + zones_macro

    # Confluence
    result = ConfluenceEngine.compute_total(
        df=df,
        symbol_cfg=symbol_cfg,
        zones=all_zones,
        tolerance=zone_cfg["tolerance"]
    )
    current_position = None
    signal = SignalGenerator.from_confluence(
        symbol="EURUSD",
        timeframe=mt5.TIMEFRAME_M5,
        df=df,
        confluence=result,
    )

    print(signal)
    decision = StrategyEngine.evaluate(df, signal, strategy_cfg, current_position)
    print(decision)


    print("\n--- Confluence Result ---")
    print("Pattern score:", result["pattern_score"])
    print("Zone score:", result["zone_score"])
    print("Volatility score:", result["volatility_score"])
    print("TOTAL:", result["total"])
    print("-------------------------\n")

    print("Last candle:")
    print(df.tail(1))
