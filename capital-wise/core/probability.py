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


class ProbabilityEngine:
    """
    CAPITAL WISE
    Historical Probability Engine

    لا يعتبر probability prediction.
    بل يقدّر الاحتمال من observations تاريخية.
    """

    def __init__(
        self,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        confidence_level: float = 0.95,
    ):

        if prior_alpha <= 0:
            raise ValueError(
                "prior_alpha must be > 0"
            )

        if prior_beta <= 0:
            raise ValueError(
                "prior_beta must be > 0"
            )

        if not 0.50 < confidence_level < 1.0:
            raise ValueError(
                "confidence_level must be between 0.5 and 1"
            )

        self.alpha = prior_alpha
        self.beta = prior_beta
        self.confidence_level = confidence_level

    def estimate(
        self,
        wins: int,
        losses: int,
    ) -> ProbabilityResult:

        if wins < 0 or losses < 0:
            raise ValueError(
                "wins/losses cannot be negative"
            )

        observations = wins + losses

        if observations == 0:
            raise ValueError(
                "at least one observation required"
            )

        posterior_alpha = (
            self.alpha + wins
        )

        posterior_beta = (
            self.beta + losses
        )

        probability = (
            posterior_alpha
            /
            (
                posterior_alpha
                + posterior_beta
            )
        )

        lower, upper = (
            self._wilson_interval(
                wins=wins,
                losses=losses,
            )
        )

        return ProbabilityResult(
            observations=observations,
            wins=wins,
            losses=losses,
            probability=probability,
            lower_bound=lower,
            upper_bound=upper,
            confidence_level=self.confidence_level,
        )

    def _wilson_interval(
        self,
        wins: int,
        losses: int,
    ) -> tuple[float, float]:

        n = wins + losses

        p = wins / n

        # 95% تقريبًا
        z = 1.96

        denominator = (
            1.0 + z**2 / n
        )

        center = (
            p
            + z**2 / (2.0 * n)
        ) / denominator

        margin = (
            z
            * sqrt(
                (
                    p * (1.0 - p) / n
                )
                +
                z**2 / (4.0 * n**2)
            )
            / denominator
        )

        return (
            max(0.0, center - margin),
            min(1.0, center + margin),
        )
