from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EVResult:
    probability: float

    reward_r: float
    risk_r: float

    gross_ev_r: float

    transaction_cost_r: float
    net_ev_r: float

    expectancy_per_trade: float

    break_even_probability: float
    edge_probability: float

    profitable: bool


class ExpectedValueEngine:
    """
    CAPITAL WISE
    Expected Value Engine

    R = مقدار المخاطرة في الصفقة.
    """

    def calculate(
        self,
        probability: float,
        reward_r: float = 3.0,
        risk_r: float = 1.0,
        transaction_cost_r: float = 0.0,
    ) -> EVResult:

        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "probability must be between 0 and 1"
            )

        if reward_r <= 0:
            raise ValueError(
                "reward_r must be > 0"
            )

        if risk_r <= 0:
            raise ValueError(
                "risk_r must be > 0"
            )

        if transaction_cost_r < 0:
            raise ValueError(
                "transaction_cost_r cannot be negative"
            )

        loss_probability = (
            1.0 - probability
        )

        gross_ev = (
            probability * reward_r
            -
            loss_probability * risk_r
        )

        net_ev = (
            gross_ev
            -
            transaction_cost_r
        )

        # نقطة التعادل بدون تكاليف.
        break_even = (
            risk_r
            /
            (reward_r + risk_r)
        )

        edge = (
            probability
            - break_even
        )

        # قيمة R المتوقعة لكل صفقة.
        expectancy = net_ev

        return EVResult(
            probability=probability,
            reward_r=reward_r,
            risk_r=risk_r,
            gross_ev_r=gross_ev,
            transaction_cost_r=transaction_cost_r,
            net_ev_r=net_ev,
            expectancy_per_trade=expectancy,
            break_even_probability=break_even,
            edge_probability=edge,
            profitable=net_ev > 0.0,
        )
