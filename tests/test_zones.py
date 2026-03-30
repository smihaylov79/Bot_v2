from core.config_loader import ConfigLoader
from trading_core.zones import Zones
from core.mt5_feed import MT5Feed
import MetaTrader5 as mt5

def run():
    print("Testing Zones...")

    cfg = ConfigLoader().load_all()
    zcfg = cfg["strategies"]["zones"]

    feed = MT5Feed()
    feed.initialize()
    df = feed.get_ohlcv("EURUSD", mt5.TIMEFRAME_M5, 300)
    feed.shutdown()

    # Micro swings
    df_micro = Zones.find_swings(df,
                                 left=zcfg["micro"]["left"],
                                 right=zcfg["micro"]["right"])

    # Macro swings
    df_macro = Zones.find_swings(df,
                                 left=zcfg["macro"]["left"],
                                 right=zcfg["macro"]["right"])

    zones_micro = Zones.cluster_zones(df_micro, tolerance=zcfg["tolerance"])
    zones_macro = Zones.cluster_zones(df_macro, tolerance=zcfg["tolerance"])

    print("Micro zones:", zones_micro)
    print("Macro zones:", zones_macro)

