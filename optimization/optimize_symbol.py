import optuna
import pandas as pd

from backtest.metrics import BacktestMetrics
from core.config_loader import ConfigLoader
from utils.config import load_yaml, deep_merge
from storage.storage import MarketDataStorage
from storage.backtest_logs import BacktestStorage
from analysis.historical_signals import HistoricalSignalGenerator
from backtest.engine import BacktestEngine


loader = ConfigLoader()

cfg_general = loader.load("general.yaml")      # same as in your backtest
cfg_strategies = loader.load("strategies.yaml")
cfg_symbols = loader.load("symbols.yaml")      # if you need it later

# our new per-symbol fib/confluence config
strategy_cfg = loader.load("strategy_config.yaml")
default_cfg = strategy_cfg["default"]

market_store = MarketDataStorage()
bt_store = BacktestStorage()


def objective(trial):
    symbol = "[SP500]"
    timeframe = "M5"

    # 1) Suggest params
    trial_params = {
        "pattern_weights": {
            "bullish_engulfing": trial.suggest_int("bullish_engulfing", -2, 3),
            "bearish_engulfing": trial.suggest_int("bearish_engulfing", -3, 2),
        },
        "zones": {
            "tolerance": trial.suggest_float("tolerance", 0.0005, 0.0030),
        },
        "volatility": {
            "atr_period": trial.suggest_int("atr_period", 7, 28),
        },
        "trend": {
            "ma_fast": trial.suggest_int("ma_fast", 5, 30),
            "ma_slow": trial.suggest_int("ma_slow", 20, 80),
        },
        "strategy": {
            "min_score": trial.suggest_int("min_score", 1, 4),
            "min_confidence": trial.suggest_float("min_confidence", 0.1, 0.8),
            "require_trend_alignment": trial.suggest_categorical("require_trend_alignment", [True, False]),
            "sl_atr_multiplier": trial.suggest_float("sl_atr_multiplier", 1.0, 4.0),
            "tp_atr_multiplier": trial.suggest_float("tp_atr_multiplier", 1.0, 6.0),
            "exit_score": trial.suggest_int("exit_score", -2, 0),
        },
    }

    # 2) Merge defaults + trial params
    symbol_cfg = deep_merge(default_cfg, trial_params)

    # 3) Build runtime config in the shape ConfluenceEngine expects
    runtime_cfg = dict(symbol_cfg)  # shallow copy is enough for keys
    runtime_cfg["bullish"] = symbol_cfg["patterns"]["bullish"]
    runtime_cfg["bearish"] = symbol_cfg["patterns"]["bearish"]
    runtime_cfg["neutral"] = symbol_cfg["patterns"]["neutral"]

    # 4) Load candles
    df = market_store.load_candles(symbol, timeframe)
    if df.empty or len(df) < 200:
        return -1e9


    # 5) Generate signals using runtime_cfg
    hsg = HistoricalSignalGenerator(runtime_cfg)
    df_signals = hsg.generate(df, symbol, timeframe)


    # 6) Build config_strategy for BacktestEngine
    config_strategy = {
        "strategy": runtime_cfg["strategy"]
    }

    engine = BacktestEngine(
        config_general=cfg_general,
        config_strategy=config_strategy,
    )
    trades = engine.run(df_signals, symbol)
    metrics = BacktestMetrics.compute(trades)

    start_timestamp = pd.to_datetime(df.index.min(), unit="s", utc=True).isoformat()
    end_timestamp = pd.to_datetime(df.index.max(), unit="s", utc=True).isoformat()

    # 7) Save trial
    bt_store.save_result(
        symbol=symbol,
        timeframe=timeframe,
        symbol_cfg=runtime_cfg,
        metrics=metrics,
        optimization_id="SP500_M5_v1",
        trial_number=trial.number,
        optimizer="optuna",
        search_space=trial_params,
        num_candles=len(df),
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp
    )

    # 8) Objective
    return metrics["expectancy"]



# ---------------------------------------------------------
# Run optimization
# ---------------------------------------------------------
def run_optimization():
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=3)

    print("Best trial:", study.best_trial.number)
    print("Best value:", study.best_value)
    print("Best params:", study.best_params)

    best = study.best_trial

    conn = bt_store._connect()
    c = conn.cursor()

    c.execute("""
        UPDATE backtests
        SET is_best = 1
        WHERE optimization_id = ? AND trial_number = ?
    """, ("SP500_M5_v1", best.number))

    conn.commit()
    conn.close()

    print("Best trial marked in DB:", best.number)


if __name__ == "__main__":
    run_optimization()

