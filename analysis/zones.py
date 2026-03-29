# analysis/zones.py

import pandas as pd
import numpy as np


class Zones:
    @staticmethod
    def find_swings(df: pd.DataFrame, left: int, right: int):
        """
        Detects swing highs and swing lows.
        left/right define how many candles on each side must be lower/higher.
        """

        df = df.copy()
        highs = df["high"].values
        lows = df["low"].values

        swing_highs = []
        swing_lows = []

        for i in range(left, len(df) - right):
            if highs[i] == max(highs[i-left:i+right+1]):
                swing_highs.append(i)
            if lows[i] == min(lows[i-left:i+right+1]):
                swing_lows.append(i)

        df["is_swing_high"] = False
        df["is_swing_low"] = False

        # df.loc[swing_highs, "is_swing_high"] = True
        # df.loc[swing_lows, "is_swing_low"] = True
        df.iloc[swing_highs, df.columns.get_loc("is_swing_high")] = True
        df.iloc[swing_lows, df.columns.get_loc("is_swing_low")] = True

        return df

    @staticmethod
    def cluster_zones(df: pd.DataFrame, tolerance: float = 0.0005):
        """
        Clusters swing highs/lows into support/resistance zones.
        tolerance defines how close levels must be to be merged.
        """

        swing_levels = []

        for idx, row in df[df["is_swing_high"]].iterrows():
            swing_levels.append(row["high"])

        for idx, row in df[df["is_swing_low"]].iterrows():
            swing_levels.append(row["low"])

        swing_levels = sorted(swing_levels)

        zones = []
        current_zone = [swing_levels[0]]

        for level in swing_levels[1:]:
            if abs(level - current_zone[-1]) <= tolerance:
                current_zone.append(level)
            else:
                zones.append((min(current_zone), max(current_zone)))
                current_zone = [level]

        zones.append((min(current_zone), max(current_zone)))

        return zones

    @staticmethod
    def find_liquidity_zones(df: pd.DataFrame, tolerance: float = 0.0003):
        """
        Detects equal highs/lows (liquidity pools).
        """

        df = df.copy()
        highs = df["high"].round(5)
        lows = df["low"].round(5)

        liquidity_highs = highs[highs.duplicated(keep=False)]
        liquidity_lows = lows[lows.duplicated(keep=False)]

        high_zones = []
        low_zones = []

        if len(liquidity_highs) > 0:
            high_zones = Zones._cluster_levels(liquidity_highs.tolist(), tolerance)

        if len(liquidity_lows) > 0:
            low_zones = Zones._cluster_levels(liquidity_lows.tolist(), tolerance)

        return {
            "liquidity_highs": high_zones,
            "liquidity_lows": low_zones
        }

    @staticmethod
    def _cluster_levels(levels, tolerance):
        """
        Helper for clustering liquidity levels.
        """

        levels = sorted(levels)
        clusters = []
        current = [levels[0]]

        for lvl in levels[1:]:
            if abs(lvl - current[-1]) <= tolerance:
                current.append(lvl)
            else:
                clusters.append((min(current), max(current)))
                current = [lvl]

        clusters.append((min(current), max(current)))
        return clusters
