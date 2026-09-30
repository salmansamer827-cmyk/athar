from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketState:
    migration_score: float
    expansion_score: float
    balance_score: float
    concentration_score: float

    state: str
    confidence: float


class MarketStateEngine:

    def calculate(
        self,
        poc_velocity: float,
        value_area_width_change: float,
        value_location: float,
        entropy: float,
        concentration: float,
    ) -> MarketState:

        # ----------------------------------------
        # Migration
        # ----------------------------------------

        migration_score = (
            0.50 * self._bounded_score(
                poc_velocity
            )
            +
            0.30 * self._bounded_score(
                value_location - 0.50
            )
            +
            0.20 * self._bounded_score(
                value_area_width_change
            )
        )

        # ----------------------------------------
        # Expansion
        # ----------------------------------------

        expansion_score = (
            self._bounded_score(
                value_area_width_change
            )
        )

        # ----------------------------------------
        # Balance
        # ----------------------------------------

        balance_score = (
            1.0
            - min(
                1.0,
                abs(
                    migration_score
                )
            )
        )

        # ----------------------------------------
        # Concentration
        # ----------------------------------------

        concentration_score = min(
            1.0,
            max(
                0.0,
                concentration,
            ),
        )

        # ----------------------------------------
        # State
        # ----------------------------------------

        if migration_score > 0.35:

            state = (
                "VALUE_MIGRATION_UP"
            )

        elif migration_score < -0.35:

            state = (
                "VALUE_MIGRATION_DOWN"
            )

        elif expansion_score > 0.35:

            state = "VALUE_EXPANSION"

        elif expansion_score < -0.35:

            state = "VALUE_CONTRACTION"

        else:

            state = "BALANCED"

        confidence = min(
            1.0,
            abs(migration_score)
            + 0.5 * abs(expansion_score)
            + 0.25 * concentration_score,
        )

        return MarketState(
            migration_score=migration_score,
            expansion_score=expansion_score,
            balance_score=balance_score,
            concentration_score=concentration_score,
            state=state,
            confidence=confidence,
        )

    @staticmethod
    def _bounded_score(
        value: float,
    ) -> float:

        # تحويل مستقر إلى [-1, +1]
        return value / (
            1.0 + abs(value)
        )
