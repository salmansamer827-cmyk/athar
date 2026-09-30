from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveRiskResult:
    risk_percent: float
    reward_risk: float

    volatility_factor: float
    probability_factor: float
    uncertainty_factor: float
    drawdown_factor: float

    risk_score: float
    allowed: bool


class AdaptiveRiskEngine:
    """
    CAPITAL WISE / EXCORA

    Adaptive risk controller.

    Inputs:
        probability
        uncertainty
        volatility_ratio
        drawdown_percent

    Outputs:
        risk_percent
        reward_risk
        allowed
    """

    def __init__(
        self,
        base_risk_percent: float = 0.01,
        base_reward_risk: float = 3.0,
        min_risk_percent: float = 0.0025,
        max_risk_percent: float = 0.02,
    ) -> None:

        if not 0 < min_risk_percent <= max_risk_percent:
            raise ValueError(
                "Invalid risk limits"
            )

        if not min_risk_percent <= base_risk_percent <= max_risk_percent:
            raise ValueError(
                "base_risk_percent must be inside risk limits"
            )

        if base_reward_risk <= 0:
            raise ValueError(
                "base_reward_risk must be > 0"
            )

        self.base_risk_percent = float(
            base_risk_percent
        )

        self.base_reward_risk = float(
            base_reward_risk
        )

        self.min_risk_percent = float(
            min_risk_percent
        )

        self.max_risk_percent = float(
            max_risk_percent
        )

    def calculate(
        self,
        probability: float,
        uncertainty: float,
        volatility_ratio: float = 1.0,
        drawdown_percent: float = 0.0,
    ) -> AdaptiveRiskResult:

        self._validate_probability(
            probability
        )

        self._validate_uncertainty(
            uncertainty
        )

        if volatility_ratio <= 0:
            raise ValueError(
                "volatility_ratio must be > 0"
            )

        if drawdown_percent < 0:
            raise ValueError(
                "drawdown_percent must be >= 0"
            )

        # --------------------------------------------------
        # 1. VOLATILITY
        # --------------------------------------------------

        if volatility_ratio >= 2.0:
            volatility_factor = 0.50

        elif volatility_ratio >= 1.5:
            volatility_factor = 0.70

        elif volatility_ratio >= 1.20:
            volatility_factor = 0.85

        elif volatility_ratio <= 0.70:
            volatility_factor = 0.85

        else:
            volatility_factor = 1.00

        # --------------------------------------------------
        # 2. PROBABILITY
        # --------------------------------------------------

        if probability < 0.50:
            probability_factor = 0.50

        elif probability < 0.55:
            probability_factor = 0.70

        elif probability < 0.60:
            probability_factor = 0.85

        elif probability < 0.65:
            probability_factor = 1.00

        elif probability < 0.70:
            probability_factor = 1.10

        else:
            probability_factor = 1.20

        # --------------------------------------------------
        # 3. UNCERTAINTY
        # --------------------------------------------------

        uncertainty_factor = max(
            0.25,
            1.0 - uncertainty,
        )

        # --------------------------------------------------
        # 4. DRAWDOWN
        # --------------------------------------------------

        if drawdown_percent >= 15.0:
            drawdown_factor = 0.40

        elif drawdown_percent >= 10.0:
            drawdown_factor = 0.60

        elif drawdown_percent >= 5.0:
            drawdown_factor = 0.80

        else:
            drawdown_factor = 1.00

        # --------------------------------------------------
        # 5. COMBINED RISK
        # --------------------------------------------------

        multiplier = (
            volatility_factor
            * probability_factor
            * uncertainty_factor
            * drawdown_factor
        )

        risk_percent = (
            self.base_risk_percent
            * multiplier
        )

        risk_percent = min(
            self.max_risk_percent,
            max(
                self.min_risk_percent,
                risk_percent,
            ),
        )

        # --------------------------------------------------
        # 6. RISK SCORE
        # --------------------------------------------------

        risk_score = (
            probability
            * 100.0
            * (1.0 - uncertainty)
            * volatility_factor
            * drawdown_factor
        )

        risk_score = min(
            100.0,
            max(
                0.0,
                risk_score,
            ),
        )

        # --------------------------------------------------
        # 7. EXECUTION PERMISSION
        # --------------------------------------------------

        allowed = (
            probability >= 0.55
            and uncertainty <= 0.25
            and drawdown_percent < 15.0
            and volatility_ratio < 3.0
        )

        # --------------------------------------------------
        # 8. ADAPTIVE RR
        # --------------------------------------------------

        if (
            probability >= 0.70
            and uncertainty <= 0.15
        ):
            reward_risk = 3.5

        elif (
            probability >= 0.65
            and uncertainty <= 0.20
        ):
            reward_risk = 3.0

        elif (
            probability >= 0.60
            and uncertainty <= 0.25
        ):
            reward_risk = 2.5

        else:
            reward_risk = 2.0

        return AdaptiveRiskResult(
            risk_percent=risk_percent,
            reward_risk=reward_risk,
            volatility_factor=volatility_factor,
            probability_factor=probability_factor,
            uncertainty_factor=uncertainty_factor,
            drawdown_factor=drawdown_factor,
            risk_score=risk_score,
            allowed=allowed,
        )

    @staticmethod
    def _validate_probability(
        probability: float,
    ) -> None:

        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "probability must be between 0 and 1"
            )

    @staticmethod
    def _validate_uncertainty(
        uncertainty: float,
    ) -> None:

        if not 0.0 <= uncertainty <= 1.0:
            raise ValueError(
                "uncertainty must be between 0 and 1"
            )
