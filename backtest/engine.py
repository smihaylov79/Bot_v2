import pandas as pd
import numpy as np


class BacktestEngine:

    def __init__(self, config_general, config_strategy):
        self.risk_per_trade = config_general["trading"]["risk_per_trade"]
        self.min_score = config_strategy["strategy"]["min_score"]
        self.min_confidence = config_strategy["strategy"]["min_confidence"]
        self.require_trend_alignment = config_strategy["strategy"]["require_trend_alignment"]
        self.sl_atr_multiplier = config_strategy["strategy"]["sl_atr_multiplier"]
        self.tp_atr_multiplier = config_strategy["strategy"]["tp_atr_multiplier"]
        self.exit_score = config_strategy["strategy"]["exit_score"]

    # ---------------------------------------------------------
    # ATR calculation
    # ---------------------------------------------------------
    @staticmethod
    def compute_atr(df, period=14):
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr

    # ---------------------------------------------------------
    # Main backtest
    # ---------------------------------------------------------
    def run(self, df, symbol):

        df = df.copy()
        df["atr"] = self.compute_atr(df)

        trades = []
        equity = 1.0  # normalized equity
        position = None

        for i in range(50, len(df)):

            row = df.iloc[i]
            prev = df.iloc[i - 1]

            # ---------------------------------------------
            # EXIT LOGIC (if in position)
            # ---------------------------------------------
            if position is not None:

                # Early exit if confluence collapses
                if row["total_score"] <= self.exit_score:
                    exit_price = row["close"]
                    pnl = (exit_price - position["entry_price"]) * position["direction"]
                    equity += pnl * position["size"]

                    position["exit_price"] = exit_price
                    position["exit_time"] = row.name
                    position["pnl"] = pnl
                    trades.append(position)
                    position = None
                    continue

                # SL/TP logic
                if position["direction"] == 1:  # long
                    if row["low"] <= position["sl"]:
                        exit_price = position["sl"]
                    elif row["high"] >= position["tp"]:
                        exit_price = position["tp"]
                    else:
                        exit_price = None

                else:  # short
                    if row["high"] >= position["sl"]:
                        exit_price = position["sl"]
                    elif row["low"] <= position["tp"]:
                        exit_price = position["tp"]
                    else:
                        exit_price = None

                if exit_price is not None:
                    pnl = (exit_price - position["entry_price"]) * position["direction"]
                    equity += pnl * position["size"]

                    position["exit_price"] = exit_price
                    position["exit_time"] = row.name
                    position["pnl"] = pnl
                    trades.append(position)
                    position = None
                    continue

            # ---------------------------------------------
            # ENTRY LOGIC
            # ---------------------------------------------
            if position is None:

                # Must meet min score
                if abs(row["total_score"]) < self.min_score:
                    continue

                # Must meet confidence
                if row["confidence"] < self.min_confidence:
                    continue

                # Trend alignment (optional)
                if self.require_trend_alignment:
                    if np.sign(row["trend_score"]) != np.sign(row["total_score"]):
                        continue

                # Determine direction
                direction = 1 if row["signal"] == 1 else -1 if row["signal"] == -1 else 0
                if direction == 0:
                    continue

                # ATR-based SL/TP
                atr = row["atr"]
                if np.isnan(atr):
                    continue

                sl = row["close"] - direction * atr * self.sl_atr_multiplier
                tp = row["close"] + direction * atr * self.tp_atr_multiplier

                # Position sizing
                risk_amount = equity * self.risk_per_trade
                stop_distance = abs(row["close"] - sl)
                size = risk_amount / stop_distance if stop_distance > 0 else 0

                position = {
                    "symbol": symbol,
                    "entry_time": row.name,
                    "entry_price": row["close"],
                    "direction": direction,
                    "sl": sl,
                    "tp": tp,
                    "size": size,
                }

        return pd.DataFrame(trades)
