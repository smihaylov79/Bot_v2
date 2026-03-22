# strategy_engine.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from analysis.signals import Signal


@dataclass
class TradeDecision:
    action: str              # "enter_long", "enter_short", "exit", "hold", "skip"
    direction: Optional[str] # "long" or "short"
    sl: Optional[float]
    tp: Optional[float]
    reason: str
    metadata: Dict[str, Any]


class StrategyEngine:

    @staticmethod
    def should_enter(signal: Signal, cfg: dict) -> bool:
        """
        Basic entry rule:
        - abs(total_score) >= min_score
        - confidence >= min_confidence
        Trend alignment is optional and controlled by config.
        """

        if abs(signal.total_score) < cfg["min_score"]:
            return False

        if signal.confidence < cfg["min_confidence"]:
            return False

        # Optional trend alignment
        if cfg.get("require_trend_alignment", False):
            if signal.direction == "long" and signal.trend_score <= 0:
                return False
            if signal.direction == "short" and signal.trend_score >= 0:
                return False

        return True

    @staticmethod
    def compute_sl_tp(price: float, atr: float, cfg: dict) -> (float, float):
        """
        ATR-based SL/TP.
        """
        sl_mult = cfg["sl_atr_multiplier"]
        tp_mult = cfg["tp_atr_multiplier"]

        sl = price - atr * sl_mult
        tp = price + atr * tp_mult

        return sl, tp

    @staticmethod
    def evaluate(
        df,
        signal: Signal,
        cfg: dict,
        current_position: Optional[str] = None,
    ) -> TradeDecision:

        last = df.iloc[-1]
        atr = last.get("atr", None)

        # No ATR → cannot compute SL/TP
        if atr is None:
            return TradeDecision(
                action="skip",
                direction=None,
                sl=None,
                tp=None,
                reason="ATR missing",
                metadata={}
            )

        # If no open position → check entry
        if current_position is None:
            if StrategyEngine.should_enter(signal, cfg):
                sl, tp = StrategyEngine.compute_sl_tp(signal.price, atr, cfg)

                return TradeDecision(
                    action=f"enter_{signal.direction}",
                    direction=signal.direction,
                    sl=sl,
                    tp=tp,
                    reason="Entry conditions met",
                    metadata={"confidence": signal.confidence}
                )

            return TradeDecision(
                action="skip",
                direction=None,
                sl=None,
                tp=None,
                reason="Entry conditions not met",
                metadata={}
            )

        # If already in a position → simple exit rule
        if current_position == "long":
            if signal.direction == "short" and abs(signal.total_score) >= cfg["exit_score"]:
                return TradeDecision(
                    action="exit",
                    direction=None,
                    sl=None,
                    tp=None,
                    reason="Opposite signal strong enough",
                    metadata={}
                )

        if current_position == "short":
            if signal.direction == "long" and abs(signal.total_score) >= cfg["exit_score"]:
                return TradeDecision(
                    action="exit",
                    direction=None,
                    sl=None,
                    tp=None,
                    reason="Opposite signal strong enough",
                    metadata={}
                )

        return TradeDecision(
            action="hold",
            direction=current_position,
            sl=None,
            tp=None,
            reason="Holding position",
            metadata={}
        )
