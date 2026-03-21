# analysis/candles.py

import pandas as pd


class CandleMetrics:
    @staticmethod
    def compute_basic(df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds basic candle metrics:
        - body_size
        - upper_wick
        - lower_wick
        - range
        - direction (1 = bullish, -1 = bearish, 0 = doji)
        """

        df = df.copy()

        df["body_size"] = (df["close"] - df["open"]).abs()
        df["range"] = df["high"] - df["low"]

        df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
        df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]

        df["direction"] = df.apply(
            lambda row: 1 if row["close"] > row["open"]
            else -1 if row["close"] < row["open"]
            else 0,
            axis=1
        )

        return df

    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Adds ATR (Average True Range) to the DataFrame.
        """

        df = df.copy()

        df["tr"] = df["high"] - df["low"]
        df["atr"] = df["tr"].rolling(period).mean()

        return df

    @staticmethod
    def detect_impulse(df, multiplier=1.5, atr_period=14):
        df = df.copy()

        if "atr" not in df.columns:
            df = CandleMetrics.add_atr(df, period=atr_period)

        df["is_impulse"] = df["range"] > df["atr"] * multiplier
        return df

