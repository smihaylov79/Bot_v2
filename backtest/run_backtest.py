from storage.storage import MarketDataStorage
# from analysis.historical_signals import HistoricalSignalGenerator
from backtest.engine import BacktestEngine
from backtest.metrics import BacktestMetrics
from core.config_loader import ConfigLoader
from trading_core.historical_signals import HistoricalSignalGenerator


def run_single_backtest(symbol="[SP500]", timeframe="M5"):

    # Load configs
    loader = ConfigLoader()
    cfg_general = loader.load("general.yaml")
    cfg_strategy = loader.load("strategies.yaml")
    cfg_symbols = loader.load("symbols.yaml")

    # Load symbol-specific pattern config
    symbol_cfg = cfg_symbols[symbol]["patterns"]

    # Load candles
    db = MarketDataStorage()
    df = db.load_candles(symbol, timeframe)
    # print(f'Number of candles: {len(df)}')
    # print(df.tail(5))

    # Generate historical signals
    hsg = HistoricalSignalGenerator(symbol_cfg)
    df = hsg.generate(df, symbol, timeframe)

    print(df["total_score"].value_counts())
    print(df["signal"].value_counts())
    print(df[["pattern_score", "zone_score", "volatility_score", "trend_score", "total_score"]].head(20))
    print("Pattern score distribution:")
    print(df["pattern_score"].value_counts())
    print("Volatility score distribution:")
    print(df["volatility_score"].value_counts())
    print("Trend score distribution:")
    print(df["trend_score"].value_counts())

    # Run backtest
    engine = BacktestEngine(cfg_general, cfg_strategy)
    trades = engine.run(df, symbol)

    # Compute metrics
    metrics = BacktestMetrics.compute(trades)

    for k, v in metrics.items():
        print(f"{k}: {v}")

    # print(metrics)
    return trades, metrics


if __name__ == "__main__":
    run_single_backtest()
