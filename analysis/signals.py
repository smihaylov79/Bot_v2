# analysis/signal.py

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Signal:
    symbol: str
    direction: str          # "long", "short", "neutral"
    total_score: int
    pattern_score: int
    zone_score: int
    volatility_score: int
    trend_score: int
    confidence: float       # 0.0–1.0
    price: float
    timeframe: str
    metadata: Dict[str, Any]


class SignalGenerator:

    @staticmethod
    def determine_direction(total_score: int) -> str:
        if total_score > 0:
            return "long"
        if total_score < 0:
            return "short"
        return "neutral"

    @staticmethod
    def compute_confidence(total_score: int, max_score: int = 6) -> float:
        """
        Map absolute score to [0, 1].
        Example: max_score = 6 → |score|=6 => 1.0, |score|=3 => 0.5
        """
        score_abs = abs(total_score)
        return min(1.0, score_abs / max_score)

    @staticmethod
    def from_confluence(
        symbol: str,
        timeframe: str,
        df,
        confluence: Dict[str, int],
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Signal:

        last = df.iloc[-1]
        total = confluence["total"]

        direction = SignalGenerator.determine_direction(total)
        confidence = SignalGenerator.compute_confidence(total)

        metadata = {
            "timestamp": last.name,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return Signal(
            symbol=symbol,
            direction=direction,
            total_score=total,
            pattern_score=confluence["pattern_score"],
            zone_score=confluence["zone_score"],
            volatility_score=confluence["volatility_score"],
            trend_score=confluence["trend_score"],
            confidence=confidence,
            price=last["close"],
            timeframe=str(timeframe),
            metadata=metadata,
        )
