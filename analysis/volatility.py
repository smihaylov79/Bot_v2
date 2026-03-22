# analysis/volatility.py

import pandas as pd
import numpy as np


class Volatility:

    # ---------------------------------------------------------
    # ATR
    # ---------------------------------------------------------
    @staticmethod
    def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        df = df.copy()

        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift(1)).abs()
        low_close = (df["low"] - df["close"].shift(1)).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(period).mean()

        return df

    # ---------------------------------------------------------
    # ATR Percentile Regime
    # ---------------------------------------------------------
    @staticmethod
    def compute_atr_percentile(df: pd.DataFrame, window: int = 200) -> pd.DataFrame:
        df = df.copy()

        df["atr_percentile"] = (
            df["atr"]
            .rolling(window)
            .apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)
        )

        return df

    # ---------------------------------------------------------
    # Expansion / Compression
    # ---------------------------------------------------------
    @staticmethod
    def compute_volatility_state(
        df: pd.DataFrame,
        expansion_factor: float = 1.5,
        compression_factor: float = 0.7,
    ) -> pd.DataFrame:

        df = df.copy()

        df["vol_expansion"] = df["range"] > df["atr"] * expansion_factor
        df["vol_compression"] = df["range"] < df["atr"] * compression_factor

        return df

    # ---------------------------------------------------------
    # Volatility Score (for confluence)
    # ---------------------------------------------------------
    @staticmethod
    def compute_volatility_score(df: pd.DataFrame) -> int:
        last = df.iloc[-1]

        if last.get("vol_expansion", False):
            return +1
        if last.get("vol_compression", False):
            return -1

        return 0

    # ---------------------------------------------------------
    # Master function
    # ---------------------------------------------------------
    @staticmethod
    def compute_all(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        df = Volatility.compute_atr(df, cfg["atr_period"])
        df = Volatility.compute_atr_percentile(df, cfg["percentile_window"])
        df = Volatility.compute_volatility_state(
            df,
            cfg["expansion_factor"],
            cfg["compression_factor"],
        )
        return df
