from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DrawdownSnapshot:
    equity: float
    peak_equity: float

    drawdown_amount: float
    drawdown_percent: float

    max_drawdown_amount: float
    max_drawdown_percent: float

    recovery_percent: float


class DrawdownEngine:
    """
    CAPITAL WISE

    Equity curve and drawdown analytics.
    """

    def __init__(
        self,
        initial_equity: float,
    ):

        if initial_equity <= 0:
            raise ValueError(
                "Initial equity must be > 0"
            )

        self.peak_equity = (
            initial_equity
        )

        self.max_drawdown_amount = 0.0
        self.max_drawdown_percent = 0.0

        self.trough_equity = (
            initial_equity
        )

    def update(
        self,
        equity: float,
    ) -> DrawdownSnapshot:

        if equity <= 0:
            raise ValueError(
                "Equity must be > 0"
            )

        if equity > self.peak_equity:

            self.peak_equity = equity
            self.trough_equity = equity

        drawdown_amount = (
            self.peak_equity - equity
        )

        drawdown_percent = (
            drawdown_amount
            / self.peak_equity
        )

        if drawdown_amount > (
            self.max_drawdown_amount
        ):

            self.max_drawdown_amount = (
                drawdown_amount
            )

        if drawdown_percent > (
            self.max_drawdown_percent
        ):

            self.max_drawdown_percent = (
                drawdown_percent
            )

            self.trough_equity = equity

        recovery_percent = 0.0

        if self.peak_equity > 0:

            recovery_percent = (
                1.0
                - (
                    drawdown_amount
                    / self.peak_equity
                )
            )

        return DrawdownSnapshot(
            equity=equity,
            peak_equity=self.peak_equity,
            drawdown_amount=drawdown_amount,
            drawdown_percent=drawdown_percent,
            max_drawdown_amount=(
                self.max_drawdown_amount
            ),
            max_drawdown_percent=(
                self.max_drawdown_percent
            ),
            recovery_percent=recovery_percent,
        )
