from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DecisionResult:
    status: str
    direction: Optional[str]

    probability: float
    expected_value: float
    market_state: str
    confidence: float

    reason: str


class QuantDecisionEngine:
    """
    CAPITAL WISE

    Final quantitative decision layer.

    This engine does NOT create arbitrary signals.

    A trade is valid only when the required
    statistical conditions are satisfied.
    """

    def __init__(
        self,
        min_probability: float = 0.60,
        min_ev_r: float = 0.50,
        min_confidence: float = 0.50,
    ):

        if not 0.0 < min_probability <= 1.0:
            raise ValueError(
                "min_probability must be between 0 and 1"
            )

        if min_ev_r < 0:
            raise ValueError(
                "min_ev_r must be >= 0"
            )

        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError(
                "min_confidence must be between 0 and 1"
            )

        self.min_probability = min_probability
        self.min_ev_r = min_ev_r
        self.min_confidence = min_confidence

    def evaluate(
        self,
        direction: Optional[str],
        probability: float,
        expected_value: float,
        market_state: str,
        confidence: float,
    ) -> DecisionResult:

        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "probability must be between 0 and 1"
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if direction is not None:
            direction = direction.upper()

            if direction not in {"LONG", "SHORT"}:
                raise ValueError(
                    "direction must be LONG, SHORT or None"
                )

        market_state = str(market_state).upper()

        if direction is None:
            return DecisionResult(
                status="NO_TRADE",
                direction=None,
                probability=probability,
                expected_value=expected_value,
                market_state=market_state,
                confidence=confidence,
                reason="No valid directional signal",
            )

        if probability < self.min_probability:
            return self._reject(
                direction,
                probability,
                expected_value,
                market_state,
                confidence,
                "Probability below threshold",
            )

        if expected_value < self.min_ev_r:
            return self._reject(
                direction,
                probability,
                expected_value,
                market_state,
                confidence,
                "Expected value below threshold",
            )

        if confidence < self.min_confidence:
            return self._reject(
                direction,
                probability,
                expected_value,
                market_state,
                confidence,
                "Market confidence below threshold",
            )

        return DecisionResult(
            status="VALID",
            direction=direction,
            probability=probability,
            expected_value=expected_value,
            market_state=market_state,
            confidence=confidence,
            reason="All quantitative thresholds passed",
        )

    @staticmethod
    def _reject(
        direction,
        probability,
        expected_value,
        market_state,
        confidence,
        reason,
    ):

        return DecisionResult(
            status="NO_TRADE",
            direction=direction,
            probability=probability,
            expected_value=expected_value,
            market_state=market_state,
            confidence=confidence,
            reason=reason,
        )
