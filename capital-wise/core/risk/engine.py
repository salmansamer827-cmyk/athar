from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    capital: float
    risk_percent: float
    risk_amount: float

    entry_price: float
    stop_price: float
    take_profit_price: float

    price_risk: float
    position_size: float
    notional_value: float

    reward_risk_ratio: float
    potential_loss: float
    potential_profit: float


class RiskEngine:
    """
    Capital Wise Risk Management Engine.

    Default:
        Risk = 1%
        Reward/Risk = 3:1
    """

    def __init__(
        self,
        risk_percent: float = 0.01,
        reward_risk: float = 3.0,
    ):
        if not 0 < risk_percent <= 0.02:
            raise ValueError(
                "risk_percent must be between 0 and 0.02"
            )

        if not 0 < reward_risk <= 20:
            raise ValueError(
                "reward_risk must be between 0 and 20"
            )

        if reward_risk <= 0:
            raise ValueError(
                "reward_risk must be > 0"
            )

        self.risk_percent = risk_percent
        self.reward_risk = reward_risk

    def calculate(
        self,
        capital: float,
        entry_price: float,
        stop_price: float,
    ) -> RiskResult:

        if capital <= 0:
            raise ValueError(
                "capital must be > 0"
            )

        if entry_price <= 0:
            raise ValueError(
                "entry_price must be > 0"
            )

        if stop_price <= 0:
            raise ValueError(
                "stop_price must be > 0"
            )

        price_risk = abs(
            entry_price - stop_price
        )

        normalized_risk = (
            price_risk / entry_price
        )

        if normalized_risk <= 0:
            raise ValueError(
                "normalized price risk must be > 0"
            )

        if normalized_risk >= 1:
            raise ValueError(
                "stop distance cannot be >= 100% of entry price"
            )

        if price_risk <= 0:
            raise ValueError(
                "entry and stop cannot be equal"
            )

        risk_amount = (
            capital * self.risk_percent
        )

        position_size = (
            risk_amount / price_risk
        )

        notional_value = (
            position_size * entry_price
        )

        if stop_price < entry_price:

            take_profit_price = (
                entry_price
                + price_risk
                * self.reward_risk
            )

        else:

            take_profit_price = (
                entry_price
                - price_risk
                * self.reward_risk
            )

        potential_loss = risk_amount

        potential_profit = (
            risk_amount
            * self.reward_risk
        )

        return RiskResult(
            capital=capital,
            risk_percent=self.risk_percent,
            risk_amount=risk_amount,
            entry_price=entry_price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            price_risk=price_risk,
            position_size=position_size,
            notional_value=notional_value,
            reward_risk_ratio=self.reward_risk,
            potential_loss=potential_loss,
            potential_profit=potential_profit,
        )
