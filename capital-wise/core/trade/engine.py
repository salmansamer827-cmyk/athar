from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.decision.engine import QuantDecisionEngine
from core.volume_profile.risk.levels import (
    ProfileRiskLevelEngine,
)
from core.risk.engine import RiskEngine


@dataclass(frozen=True)
class FinalTrade:
    status: str
    direction: Optional[str]

    entry: float
    stop_loss: float
    take_profit: float

    probability: float
    expected_value: float
    confidence: float

    risk_percent: float
    risk_amount: float
    position_size: float
    notional_value: float

    rr: float
    reason: str


class FinalTradeEngine:
    """
    CAPITAL WISE

    Final quantitative trade engine.

    Combines:

        Decision Engine
        Profile Risk Levels
        Risk Engine

    Default risk:
        1%

    Default reward/risk:
        1:3
    """

    def __init__(
        self,
        capital: float,
        risk_percent: float = 0.01,
        reward_risk: float = 3.0,
        min_probability: float = 0.60,
        min_ev_r: float = 0.50,
        min_confidence: float = 0.50,
    ):

        self.capital = capital

        self.decision_engine = QuantDecisionEngine(
            min_probability=min_probability,
            min_ev_r=min_ev_r,
            min_confidence=min_confidence,
        )

        self.profile_risk_engine = (
            ProfileRiskLevelEngine(
                volatility_buffer=0.25,
                reward_risk=reward_risk,
            )
        )

        self.risk_engine = RiskEngine(
            risk_percent=risk_percent,
            reward_risk=reward_risk,
        )

    def evaluate(
        self,
        direction: Optional[str],
        entry: float,
        profile: dict,
        probability: float,
        expected_value: float,
        market_state: str,
        confidence: float,
        nodes: list,
    ) -> FinalTrade:

        decision = self.decision_engine.evaluate(
            direction=direction,
            probability=probability,
            expected_value=expected_value,
            market_state=market_state,
            confidence=confidence,
        )

        if decision.status != "VALID":

            return FinalTrade(
                status="NO_TRADE",
                direction=decision.direction,
                entry=entry,
                stop_loss=0.0,
                take_profit=0.0,
                probability=probability,
                expected_value=expected_value,
                confidence=confidence,
                risk_percent=self.risk_engine.risk_percent,
                risk_amount=0.0,
                position_size=0.0,
                notional_value=0.0,
                rr=self.risk_engine.reward_risk,
                reason=decision.reason,
            )

        levels = self.profile_risk_engine.calculate(
            direction=direction,
            entry=entry,
            val=profile["val"],
            vah=profile["vah"],
            std=profile["std"],
            nodes=nodes,
        )

        risk = self.risk_engine.calculate(
            capital=self.capital,
            entry_price=levels.entry,
            stop_price=levels.stop_loss,
        )

        return FinalTrade(
            status="VALID",
            direction=direction.upper(),
            entry=risk.entry_price,
            stop_loss=risk.stop_price,
            take_profit=risk.take_profit_price,
            probability=probability,
            expected_value=expected_value,
            confidence=confidence,
            risk_percent=risk.risk_percent,
            risk_amount=risk.risk_amount,
            position_size=risk.position_size,
            notional_value=risk.notional_value,
            rr=risk.reward_risk_ratio,
            reason="Quantitative decision and risk validation passed",
        )
