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
        return Volatility.compute_volatility_score(df)

    # ---------------------------------------------------------
    # Trend score
    # ---------------------------------------------------------
    @staticmethod
    def compute_trend_score(df):
        from analysis.trend import Trend
        return Trend.compute_trend_score(df)

    # ---------------------------------------------------------
    # Total confluence
    # ---------------------------------------------------------
    @staticmethod
    def compute_total(df, symbol_cfg, zones, tolerance):
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

# # analysis/confluence.py
#
#
# class ConfluenceEngine:
#
#     @staticmethod
#     def compute_pattern_confluence(df, symbol_cfg):
#         """
#         Computes confluence score based on enabled patterns for the symbol.
#         """
#
#         score = 0
#         last = df.iloc[-1]
#
#         # Bullish patterns
#         for p in symbol_cfg["bullish"]:
#             if last.get(p, False):
#                 score += 1
#
#         # Bearish patterns
#         for p in symbol_cfg["bearish"]:
#             if last.get(p, False):
#                 score -= 1
#
#         # Neutral patterns (optional)
#         for p in symbol_cfg["neutral"]:
#             if last.get(p, False):
#                 score += 0  # or a small weight later
#
#         return score
#
#     @staticmethod
#     def compute_zone_confluence(df, zones, tolerance=0.0005):
#         """
#         Returns +1 if near support, -1 if near resistance.
#         """
#
#         price = df["close"].iloc[-1]
#
#         for low, high in zones:
#             if abs(price - low) <= tolerance:
#                 return +1
#             if abs(price - high) <= tolerance:
#                 return -1
#
#         return 0
#
#     @staticmethod
#     def compute_volatility_confluence(df):
#         """
#         Placeholder for volatility regime scoring.
#         """
#         if "atr" not in df.columns:
#             return 0
#
#         atr = df["atr"].iloc[-1]
#         range_ = df["range"].iloc[-1]
#
#         if range_ > atr * 1.5:
#             return +1  # expansion
#         if range_ < atr * 0.7:
#             return -1  # compression
#
#         return 0
#
#     @staticmethod
#     def compute_total(df, symbol_cfg, zones, tolerance=0.0005):
#         """
#         Combines all confluence components.
#         """
#
#         pattern_score = ConfluenceEngine.compute_pattern_confluence(df, symbol_cfg)
#         zone_score = ConfluenceEngine.compute_zone_confluence(df, zones, tolerance)
#         vol_score = ConfluenceEngine.compute_volatility_confluence(df)
#
#         return {
#             "pattern_score": pattern_score,
#             "zone_score": zone_score,
#             "volatility_score": vol_score,
#             "total": pattern_score + zone_score + vol_score
#         }
