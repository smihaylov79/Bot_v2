import optuna
import pandas as pd
from datetime import datetime, timezone

from backtest.metrics import BacktestMetrics
from core.config_loader import ConfigLoader
from utils.config import deep_merge
from storage.storage import MarketDataStorage
from storage.backtest_logs import BacktestStorage
# from analysis.historical_signals import HistoricalSignalGenerator
from backtest.engine import BacktestEngine
from trading_core.historical_signals import HistoricalSignalGenerator


# ---------------------------------------------------------
# Load configs
# ---------------------------------------------------------
loader = ConfigLoader()

cfg_general = loader.load("general.yaml")
cfg_symbols = loader.load("symbols.yaml")
strategy_cfg = loader.load("strategy_config.yaml")
default_cfg = strategy_cfg["default"]

market_store = MarketDataStorage()
bt_store = BacktestStorage()


# ---------------------------------------------------------
# Objective function
# ---------------------------------------------------------
def objective(trial, symbol, timeframe, optimization_id):
    # 1) Build dynamic pattern weight search space
    symbol_patterns = cfg_symbols[symbol]["patterns"]
    pattern_weights = {}

    # Bullish patterns
    for p in symbol_patterns["bullish"]:
        pattern_weights[p] = trial.suggest_int(p, -3, 3)

    # Bearish patterns
    for p in symbol_patterns["bearish"]:
        pattern_weights[p] = trial.suggest_int(p, -3, 3)

    # Neutral patterns (optional)
    for p in symbol_patterns["neutral"]:
        pattern_weights[p] = trial.suggest_int(p, -2, 2)

    # 2) Full trial params
    trial_params = {
        "pattern_weights": pattern_weights,

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

    # 1) Suggest parameters
    # trial_params = {
    #     "pattern_weights": {
    #         "bullish_engulfing": trial.suggest_int("bullish_engulfing", -2, 3),
    #         "bearish_engulfing": trial.suggest_int("bearish_engulfing", -3, 2),
    #     },
    #     "zones": {
    #         "tolerance": trial.suggest_float("tolerance", 0.0005, 0.0030),
    #     },
    #     "volatility": {
    #         "atr_period": trial.suggest_int("atr_period", 7, 28),
    #     },
    #     "trend": {
    #         "ma_fast": trial.suggest_int("ma_fast", 5, 30),
    #         "ma_slow": trial.suggest_int("ma_slow", 20, 80),
    #     },
    #     "strategy": {
    #         "min_score": trial.suggest_int("min_score", 1, 4),
    #         "min_confidence": trial.suggest_float("min_confidence", 0.1, 0.8),
    #         "require_trend_alignment": trial.suggest_categorical("require_trend_alignment", [True, False]),
    #         "sl_atr_multiplier": trial.suggest_float("sl_atr_multiplier", 1.0, 4.0),
    #         "tp_atr_multiplier": trial.suggest_float("tp_atr_multiplier", 1.0, 6.0),
    #         "exit_score": trial.suggest_int("exit_score", -2, 0),
    #     },
    # }

    # 2) Merge defaults + trial params
    symbol_cfg = deep_merge(default_cfg, trial_params)

    symbol_patterns = cfg_symbols[symbol]["patterns"]

    # 3) Build runtime config
    runtime_cfg = dict(symbol_cfg)
    runtime_cfg["patterns"] = symbol_patterns
    runtime_cfg["bullish"] = symbol_patterns["bullish"]
    runtime_cfg["bearish"] = symbol_patterns["bearish"]
    runtime_cfg["neutral"] = symbol_patterns["neutral"]
    # runtime_cfg = dict(symbol_cfg)
    # runtime_cfg["bullish"] = symbol_cfg["patterns"]["bullish"]
    # runtime_cfg["bearish"] = symbol_cfg["patterns"]["bearish"]
    # runtime_cfg["neutral"] = symbol_cfg["patterns"]["neutral"]

    # 4) Load candles
    df = market_store.load_candles(symbol, timeframe)
    if df.empty or len(df) < 200:
        return -1e9

    # 5) Generate signals
    hsg = HistoricalSignalGenerator(runtime_cfg)
    df_signals = hsg.generate(df, symbol, timeframe)

    # 6) Backtest
    engine = BacktestEngine(
        config_general=cfg_general,
        config_strategy={"strategy": runtime_cfg["strategy"]},
    )

    trades = engine.run(df_signals, symbol)
    metrics = BacktestMetrics.compute(trades)

    # 7) Timestamps
    start_timestamp = pd.to_datetime(df.index.min(), unit="s", utc=True).isoformat()
    end_timestamp = pd.to_datetime(df.index.max(), unit="s", utc=True).isoformat()

    # 8) Save trial
    bt_store.save_result(
        symbol=symbol,
        timeframe=timeframe,
        symbol_cfg=runtime_cfg,
        metrics=metrics,
        optimization_id=optimization_id,
        trial_number=trial.number,
        optimizer="optuna",
        search_space=trial_params,
        num_candles=len(df),
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp
    )

    return metrics["expectancy"]


# ---------------------------------------------------------
# Run optimization for ALL symbols and ALL timeframes
# ---------------------------------------------------------
def run_optimization():

    timeframes = cfg_general["timeframes"]

    for symbol, sym_cfg in cfg_symbols.items():

        if not sym_cfg.get("enabled", True):
            continue

        for timeframe in timeframes:

            # Generate unique optimization_id
            run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            optimization_id = f"{symbol}_{timeframe}_v{run_timestamp}"

            print(f"\n=== Starting optimization: {optimization_id} ===")

            study = optuna.create_study(direction="maximize")

            study.optimize(
                lambda trial: objective(trial, symbol, timeframe, optimization_id),
                n_trials=100
            )

            best = study.best_trial

            # Mark best in backtests
            conn = bt_store._connect()
            c = conn.cursor()
            c.execute("""
                UPDATE backtests
                SET is_best = 1
                WHERE optimization_id = ? AND trial_number = ?
            """, (optimization_id, best.number))
            conn.commit()
            conn.close()

            # Copy best trial into best_trials
            row = bt_store.get_trial(optimization_id, best.number)
            bt_store.save_best_trial(row)

            print(f"Best trial saved to best_trials for {optimization_id}")


if __name__ == "__main__":
    run_optimization()
