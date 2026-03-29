import pandas as pd
import numpy as np


class BacktestMetrics:

    @staticmethod
    def compute(trades: pd.DataFrame):

        # Empty case
        if trades.empty:
            return {
                "trades": 0,
                "winrate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "rr": 0,
                "expectancy": 0,
                "profit_factor": 0,
                "max_drawdown": 0,
                "equity_curve": [],

                "long_winrate": None,
                "short_winrate": None,
                "long_expectancy": None,
                "short_expectancy": None,
                "max_consecutive_losses": None,
                "max_consecutive_wins": None,
                "avg_holding_time": None,
                "median_holding_time": None,
            }

        # Normalize direction column
        trades = trades.copy()
        trades["direction"] = trades["direction"].astype(str).str.lower()

        # Basic stats
        wins = trades[trades["pnl"] > 0]
        losses = trades[trades["pnl"] < 0]

        winrate = len(wins) / len(trades)
        avg_win = wins["pnl"].mean() if not wins.empty else 0
        avg_loss = losses["pnl"].mean() if not losses.empty else 0
        rr = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
        expectancy = winrate * avg_win + (1 - winrate) * avg_loss

        gross_profit = wins["pnl"].sum()
        gross_loss = abs(losses["pnl"].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Equity curve + drawdown
        equity_curve = trades["pnl"].cumsum()
        peak = equity_curve.cummax()
        max_drawdown = (equity_curve - peak).min()

        # Long / Short metrics
        longs = trades[trades["direction"].isin(["long", "buy", "1"])]
        shorts = trades[trades["direction"].isin(["short", "sell", "-1"])]

        long_winrate = len(longs[longs["pnl"] > 0]) / len(longs) if len(longs) > 0 else None
        short_winrate = len(shorts[shorts["pnl"] > 0]) / len(shorts) if len(shorts) > 0 else None

        long_expectancy = longs["pnl"].mean() if len(longs) > 0 else None
        short_expectancy = shorts["pnl"].mean() if len(shorts) > 0 else None

        # Consecutive wins/losses
        pnl_sign = trades["pnl"].apply(lambda x: 1 if x > 0 else 0)

        max_consecutive_wins = (
            pnl_sign.groupby((pnl_sign != pnl_sign.shift()).cumsum()).cumsum().max()
        )

        max_consecutive_losses = (
            (1 - pnl_sign)
            .groupby(((1 - pnl_sign) != (1 - pnl_sign).shift()).cumsum())
            .cumsum()
            .max()
        )

        # Holding times
        holding = trades["exit_time"] - trades["entry_time"]
        avg_holding_time = holding.mean()
        median_holding_time = holding.median()

        return {
            "trades": len(trades),
            "winrate": winrate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "rr": rr,
            "expectancy": expectancy,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "equity_curve": equity_curve.tolist(),

            "long_winrate": long_winrate,
            "short_winrate": short_winrate,
            "long_expectancy": long_expectancy,
            "short_expectancy": short_expectancy,
            "max_consecutive_losses": int(max_consecutive_losses),
            "max_consecutive_wins": int(max_consecutive_wins),
            "avg_holding_time": float(avg_holding_time),
            "median_holding_time": float(median_holding_time),
        }


