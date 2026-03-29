# analysis/zone_detector.py

from analysis.zones import Zones

class ZoneDetector:

    @staticmethod
    def detect_zones(df, left=3, right=3, tolerance=0.0005):
        """
        Returns zones in the format expected by ConfluenceEngine:
        [
            {"level": x, "type": "demand"},
            {"level": y, "type": "supply"},
            ...
        ]
        """

        df_swings = Zones.find_swings(df, left, right)

        # Extract swing highs and lows
        swing_highs = df_swings[df_swings["is_swing_high"]]["high"].tolist()
        swing_lows = df_swings[df_swings["is_swing_low"]]["low"].tolist()

        # Cluster them separately
        high_clusters = Zones._cluster_levels(swing_highs, tolerance) if swing_highs else []
        low_clusters = Zones._cluster_levels(swing_lows, tolerance) if swing_lows else []

        zones = []

        # Convert clusters → zone dicts
        for lo, hi in low_clusters:
            zones.append({"level": (lo + hi) / 2, "type": "demand"})

        for lo, hi in high_clusters:
            zones.append({"level": (lo + hi) / 2, "type": "supply"})

        return zones
