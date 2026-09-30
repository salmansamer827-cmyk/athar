from __future__ import annotations

from math import sqrt

from .models import (
    BacktestMetrics,
    BacktestTrade,
    TradeOutcome,
)


class BacktestMetricsEngine:
    """
    CAPITAL WISE
    Quantitative Backtest Metrics Engine
    """

    def calculate(
        self,
        trades: list[BacktestTrade],
    ) -> BacktestMetrics:

        if not trades:
            raise ValueError(
                "trades cannot be empty"
            )

        wins = sum(
            1
            for trade in trades
            if trade.outcome == TradeOutcome.WIN
        )

        losses = sum(
            1
            for trade in trades
            if trade.outcome == TradeOutcome.LOSS
        )

        valid_trades = wins + losses

        if valid_trades == 0:
            raise ValueError(
                "No resolved trades"
            )

        win_rate = (
            wins / valid_trades
        )

        gross_profit = sum(
            max(0.0, trade.realized_r)
            for trade in trades
        )

        gross_loss = sum(
            min(0.0, trade.realized_r)
            for trade in trades
        )

        net_r = sum(
            trade.realized_r
            for trade in trades
        )

        expectancy = (
            net_r / valid_trades
        )

        if abs(gross_loss) > 0:
            profit_factor = (
                gross_profit
                / abs(gross_loss)
            )
        else:
            profit_factor = None

        max_drawdown = (
            self._maximum_drawdown(
                trades
            )
        )

        return BacktestMetrics(
            trades=valid_trades,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            gross_profit_r=gross_profit,
            gross_loss_r=gross_loss,
            net_r=net_r,
            expectancy_r=expectancy,
            profit_factor=profit_factor,
            max_drawdown_r=max_drawdown,
        )

    @staticmethod
    def _maximum_drawdown(
        trades: list[BacktestTrade],
    ) -> float:

        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for trade in trades:

            equity += trade.realized_r

            if equity > peak:
                peak = equity

            drawdown = (
                peak - equity
            )

            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown
