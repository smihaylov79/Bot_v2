# analysis/trend.py

import pandas as pd
import numpy as np


class Trend:
    # ---------------------------------------------------------
    # Moving average based trend
    # ---------------------------------------------------------
    @staticmethod
    def compute_ma_trend(
        df: pd.DataFrame,
        fast_period: int = 20,
        slow_period: int = 50,
    ) -> pd.DataFrame:
        df = df.copy()

        df["ma_fast"] = df["close"].rolling(fast_period).mean()
        df["ma_slow"] = df["close"].rolling(slow_period).mean()

        df["ma_trend_bull"] = df["ma_fast"] > df["ma_slow"]
        df["ma_trend_bear"] = df["ma_fast"] < df["ma_slow"]

        return df

    # ---------------------------------------------------------
    # Swing-based trend (HH/HL vs LH/LL)
    # Requires swing highs/lows already detected
    # ---------------------------------------------------------
    @staticmethod
    def compute_swing_trend(
        df: pd.DataFrame,
        swing_high_col: str = "swing_high",
        swing_low_col: str = "swing_low",
        lookback: int = 10,
    ) -> pd.DataFrame:
        df = df.copy()

        swing_highs = df[df[swing_high_col]].tail(lookback)
        swing_lows = df[df[swing_low_col]].tail(lookback)

        df["swing_trend_bull"] = False
        df["swing_trend_bear"] = False

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            last_highs = swing_highs["high"].tail(2).values
            last_lows = swing_lows["low"].tail(2).values

            hh_hl = (last_highs[1] > last_highs[0]) and (last_lows[1] > last_lows[0])
            lh_ll = (last_highs[1] < last_highs[0]) and (last_lows[1] < last_lows[0])

            if hh_hl:
                df.at[df.index[-1], "swing_trend_bull"] = True
            if lh_ll:
                df.at[df.index[-1], "swing_trend_bear"] = True

        return df

    # ---------------------------------------------------------
    # Trend score (for confluence)
    # ---------------------------------------------------------
    @staticmethod
    def compute_trend_score(df: pd.DataFrame) -> int:
        last = df.iloc[-1]

        score = 0

        if last.get("ma_trend_bull", False):
            score += 1
        if last.get("ma_trend_bear", False):
            score -= 1

        if last.get("swing_trend_bull", False):
            score += 1
        if last.get("swing_trend_bear", False):
            score -= 1

        return score

    # ---------------------------------------------------------
    # Master function
    # ---------------------------------------------------------
    @staticmethod
    def compute_all(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        df = Trend.compute_ma_trend(
            df,
            fast_period=cfg["ma_fast"],
            slow_period=cfg["ma_slow"],
        )

        df = Trend.compute_swing_trend(
            df,
            swing_high_col=cfg.get("swing_high_col", "swing_high"),
            swing_low_col=cfg.get("swing_low_col", "swing_low"),
            lookback=cfg.get("swing_lookback", 10),
        )

        return df
