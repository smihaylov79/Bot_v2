# analysis/confluence.py

class ConfluenceEngine:

    # ---------------------------------------------------------
    # Pattern score
    # ---------------------------------------------------------
    @staticmethod
    def compute_pattern_score(df, symbol_cfg):
        last = df.iloc[-1]
        score = 0

        for p in symbol_cfg["bullish"]:
            if last.get(p, False):
                score += 1

        for p in symbol_cfg["bearish"]:
            if last.get(p, False):
                score -= 1

        # neutral patterns do not affect score
        # print("Pattern check:", df.iloc[-1]["close"])

        return score

    # ---------------------------------------------------------
    # Zone score
    # ---------------------------------------------------------
    @staticmethod
    def compute_zone_score(df, zones, tolerance):
        last_close = df.iloc[-1]["close"]

        score = 0
        for z in zones:
            # Normalize tuple → dict
            if isinstance(z, tuple):
                level, ztype = z
            else:
                level = z["level"]
                ztype = z["type"]

            if abs(last_close - level) <= tolerance:
                if ztype == "demand":
                    score += 1
                elif ztype == "supply":
                    score -= 1

        return score

    # ---------------------------------------------------------
    # Volatility score
    # ---------------------------------------------------------
    @staticmethod
    def compute_volatility_score(df):
        from analysis.volatility import Volatility
        # print("Volatility check:", df.iloc[-1]["close"])

        return Volatility.compute_volatility_score(df)

    # ---------------------------------------------------------
    # Trend score
    # ---------------------------------------------------------
    @staticmethod
    def compute_trend_score(df):
        from analysis.trend import Trend
        # print("Trend check:", df.iloc[-1]["close"])

        return Trend.compute_trend_score(df)

    # ---------------------------------------------------------
    # Total confluence
    # ---------------------------------------------------------
    @staticmethod
    def compute_total(df, symbol_cfg, zones, tolerance):
        # print("Confluence called")

        pattern_score = ConfluenceEngine.compute_pattern_score(df, symbol_cfg)
        zone_score = ConfluenceEngine.compute_zone_score(df, zones, tolerance)
        vol_score = ConfluenceEngine.compute_volatility_score(df)
        trend_score = ConfluenceEngine.compute_trend_score(df)

        total = pattern_score + zone_score + vol_score + trend_score

        return {
            "pattern_score": pattern_score,
            "zone_score": zone_score,
            "volatility_score": vol_score,
            "trend_score": trend_score,
            "total": total,
        }
