from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EquityConfig:
    initial_capital: float = 100.0
    risk_percent: float = 0.01
    reward_risk: float = 3.0


@dataclass(frozen=True)
class TradeRiskResult:
    equity_before: float
    risk_amount: float

    realized_r: float
    pnl: float

    equity_after: float

    return_percent: float


class EquityRiskEngine:
    """
    CAPITAL WISE

    Dynamic equity and risk engine.

    Risk is calculated from current equity:

        Risk Amount = Equity × Risk %

    Therefore the system supports
    controlled compounding.
    """

    def __init__(
        self,
        config: EquityConfig | None = None,
    ):
        self.config = (
            config
            if config is not None
            else EquityConfig()
        )

        if self.config.initial_capital <= 0:
            raise ValueError(
                "Initial capital must be > 0"
            )

        if not (
            0 < self.config.risk_percent <= 1
        ):
            raise ValueError(
                "Invalid risk percent"
            )

        if self.config.reward_risk <= 0:
            raise ValueError(
                "RR must be > 0"
            )

        self.equity = (
            self.config.initial_capital
        )

    @property
    def risk_amount(self) -> float:
        return (
            self.equity
            * self.config.risk_percent
        )

    def apply_trade(
        self,
        realized_r: float,
    ) -> TradeRiskResult:

        equity_before = self.equity

        risk_amount = (
            equity_before
            * self.config.risk_percent
        )

        pnl = (
            realized_r
            * risk_amount
        )

        self.equity = (
            equity_before + pnl
        )

        return_percent = (
            pnl / equity_before
            if equity_before > 0
            else 0.0
        )

        return TradeRiskResult(
            equity_before=equity_before,
            risk_amount=risk_amount,
            realized_r=realized_r,
            pnl=pnl,
            equity_after=self.equity,
            return_percent=return_percent,
        )

    def reset(self) -> None:
        self.equity = (
            self.config.initial_capital
        )
