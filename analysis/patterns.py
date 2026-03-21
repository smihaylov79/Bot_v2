# analysis/patterns.py

import pandas as pd


# -----------------------------------------
# Pattern groups (used for confluence)
# -----------------------------------------

BULLISH_PATTERNS = [
    "bullish_engulfing",
    "hammer",
    "morning_star",
    "bullish_pin_bar",
    "bullish_three_bar_reversal",
    "bullish_breakout_bar",
    "bullish_inside_bar",
]

BEARISH_PATTERNS = [
    "bearish_engulfing",
    "shooting_star",
    "evening_star",
    "bearish_pin_bar",
    "bearish_three_bar_reversal",
    "bearish_breakout_bar",
    "bearish_inside_bar",
]

NEUTRAL_PATTERNS = [
    "doji",
    "outside_bar",
]


class Patterns:

    # ---------------------------------------------------------
    # MASTER FUNCTION — computes ALL patterns at once
    # ---------------------------------------------------------
    @staticmethod
    def detect_all(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df = Patterns.detect_engulfing(df)
        df = Patterns.detect_pinbar(df)
        df = Patterns.detect_inside_bar(df)
        df = Patterns.detect_doji(df)
        df = Patterns.detect_outside_bar(df)
        df = Patterns.detect_hammer(df)
        df = Patterns.detect_shooting_star(df)
        df = Patterns.detect_morning_star(df)
        df = Patterns.detect_evening_star(df)
        df = Patterns.detect_three_bar_reversal(df)
        df = Patterns.detect_breakout_bar(df)

        return df

    # ---------------------------------------------------------
    # ENGULFING
    # ---------------------------------------------------------
    @staticmethod
    def detect_engulfing(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["bullish_engulfing"] = (
            (df["close"] > df["open"]) &
            (df["close"].shift(1) < df["open"].shift(1)) &
            (df["close"] > df["open"].shift(1)) &
            (df["open"] < df["close"].shift(1))
        )

        df["bearish_engulfing"] = (
            (df["close"] < df["open"]) &
            (df["close"].shift(1) > df["open"].shift(1)) &
            (df["close"] < df["open"].shift(1)) &
            (df["open"] > df["close"].shift(1))
        )

        return df

    # ---------------------------------------------------------
    # PIN BAR (hammer + shooting star)
    # ---------------------------------------------------------
    @staticmethod
    def detect_pinbar(df: pd.DataFrame, wick_ratio: float = 2.0) -> pd.DataFrame:
        df = df.copy()

        df["bullish_pin_bar"] = (
            (df["lower_wick"] > df["body_size"] * wick_ratio) &
            (df["upper_wick"] < df["body_size"])
        )

        df["bearish_pin_bar"] = (
            (df["upper_wick"] > df["body_size"] * wick_ratio) &
            (df["lower_wick"] < df["body_size"])
        )

        return df

    # ---------------------------------------------------------
    # INSIDE BAR
    # ---------------------------------------------------------
    @staticmethod
    def detect_inside_bar(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        inside = (
            (df["high"] < df["high"].shift(1)) &
            (df["low"] > df["low"].shift(1))
        )

        df["bullish_inside_bar"] = inside & (df["close"] > df["open"])
        df["bearish_inside_bar"] = inside & (df["close"] < df["open"])

        return df

    # ---------------------------------------------------------
    # DOJI
    # ---------------------------------------------------------
    @staticmethod
    def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
        df = df.copy()

        df["doji"] = (df["body_size"] <= df["range"] * threshold)

        return df

    # ---------------------------------------------------------
    # OUTSIDE BAR
    # ---------------------------------------------------------
    @staticmethod
    def detect_outside_bar(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["outside_bar"] = (
            (df["high"] > df["high"].shift(1)) &
            (df["low"] < df["low"].shift(1))
        )

        return df

    # ---------------------------------------------------------
    # HAMMER (bullish)
    # ---------------------------------------------------------
    @staticmethod
    def detect_hammer(df: pd.DataFrame, wick_ratio: float = 2.0) -> pd.DataFrame:
        df = df.copy()

        df["hammer"] = (
            (df["lower_wick"] > df["body_size"] * wick_ratio) &
            (df["upper_wick"] < df["body_size"]) &
            (df["close"] > df["open"])
        )

        return df

    # ---------------------------------------------------------
    # SHOOTING STAR (bearish)
    # ---------------------------------------------------------
    @staticmethod
    def detect_shooting_star(df: pd.DataFrame, wick_ratio: float = 2.0) -> pd.DataFrame:
        df = df.copy()

        df["shooting_star"] = (
            (df["upper_wick"] > df["body_size"] * wick_ratio) &
            (df["lower_wick"] < df["body_size"]) &
            (df["close"] < df["open"])
        )

        return df

    # ---------------------------------------------------------
    # MORNING STAR (bullish 3-candle pattern)
    # ---------------------------------------------------------
    @staticmethod
    def detect_morning_star(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["morning_star"] = (
            (df["close"].shift(2) < df["open"].shift(2)) &  # bearish candle
            (df["close"].shift(1) < df["open"].shift(1)) &  # small candle
            (df["close"] > df["open"]) &                    # bullish candle
            (df["close"] > df["open"].shift(2))             # closes into body of first
        )

        return df

    # ---------------------------------------------------------
    # EVENING STAR (bearish 3-candle pattern)
    # ---------------------------------------------------------
    @staticmethod
    def detect_evening_star(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["evening_star"] = (
            (df["close"].shift(2) > df["open"].shift(2)) &  # bullish candle
            (df["close"].shift(1) > df["open"].shift(1)) &  # small candle
            (df["close"] < df["open"]) &                    # bearish candle
            (df["close"] < df["open"].shift(2))             # closes into body of first
        )

        return df

    # ---------------------------------------------------------
    # THREE-BAR REVERSAL
    # ---------------------------------------------------------
    @staticmethod
    def detect_three_bar_reversal(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["bullish_three_bar_reversal"] = (
            (df["low"].shift(2) > df["low"].shift(1)) &
            (df["low"] < df["low"].shift(1)) &
            (df["close"] > df["open"])
        )

        df["bearish_three_bar_reversal"] = (
            (df["high"].shift(2) < df["high"].shift(1)) &
            (df["high"] > df["high"].shift(1)) &
            (df["close"] < df["open"])
        )

        return df

    # ---------------------------------------------------------
    # BREAKOUT BAR
    # ---------------------------------------------------------
    @staticmethod
    def detect_breakout_bar(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["bullish_breakout_bar"] = (
            (df["close"] > df["high"].shift(1)) &
            (df["close"] > df["open"])
        )

        df["bearish_breakout_bar"] = (
            (df["close"] < df["low"].shift(1)) &
            (df["close"] < df["open"])
        )

        return df
