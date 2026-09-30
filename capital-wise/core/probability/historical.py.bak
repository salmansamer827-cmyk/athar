from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class ProbabilityResult:
    observations: int
    wins: int
    losses: int

    probability: float

    lower_bound: float
    upper_bound: float

    confidence_level: float

    standard_error: float
    uncertainty: float
    adjusted_probability: float


class HistoricalProbabilityEngine:
    """
    CAPITAL WISE
    High-quality statistical probability engine.

    Uses:

        Empirical probability
        Wilson confidence interval
        Standard error
        Uncertainty estimation
        Conservative probability adjustment

    The adjusted probability is intentionally conservative:

        adjusted_probability = lower_bound

    This prevents the signal engine from treating a small
    historical sample as if its observed win rate were certain.
    """

    def calculate(
        self,
        wins: int,
        losses: int,
        confidence_level: float = 0.95,
    ) -> ProbabilityResult:

        if wins < 0 or losses < 0:
            raise ValueError("wins/losses must be >= 0")

        n = wins + losses

        if n == 0:
            raise ValueError("No observations")

        if not 0.0 < confidence_level < 1.0:
            raise ValueError("Invalid confidence level")

        p = wins / n

        z = self._z_score(confidence_level)

        denominator = 1.0 + (z * z) / n

        center = p + (z * z) / (2.0 * n)

        margin = z * sqrt(
            (p * (1.0 - p) / n)
            + (z * z / (4.0 * n * n))
        )

        lower = (center - margin) / denominator
        upper = (center + margin) / denominator

        lower = max(0.0, lower)
        upper = min(1.0, upper)

        standard_error = sqrt(
            max(
                0.0,
                p * (1.0 - p) / n,
            )
        )

        uncertainty = max(
            0.0,
            upper - lower,
        ) / 2.0

        adjusted_probability = lower

        return ProbabilityResult(
            observations=n,
            wins=wins,
            losses=losses,
            probability=p,
            lower_bound=lower,
            upper_bound=upper,
            confidence_level=confidence_level,
            standard_error=standard_error,
            uncertainty=uncertainty,
            adjusted_probability=adjusted_probability,
        )

    @staticmethod
    def _z_score(
        confidence_level: float,
    ) -> float:

        if confidence_level == 0.90:
            return 1.644854

        if confidence_level == 0.95:
            return 1.959964

        if confidence_level == 0.99:
            return 2.575829

        raise ValueError(
            "Supported confidence levels: "
            "0.90, 0.95, 0.99"
        )
