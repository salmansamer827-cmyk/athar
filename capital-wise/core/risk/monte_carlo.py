from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class MonteCarloResult:
    simulations: int

    median_final_equity: float
    worst_final_equity: float
    best_final_equity: float

    median_max_drawdown: float
    worst_max_drawdown: float

    probability_dd_5pct: float
    probability_dd_10pct: float
    probability_dd_20pct: float


class MonteCarloEngine:
    """
    CAPITAL WISE

    Monte Carlo analysis of historical R-multiples.

    The engine randomly resamples the observed
    trade outcomes while preserving the empirical
    distribution of results.
    """

    def __init__(
        self,
        initial_capital: float = 100.0,
        risk_percent: float = 0.01,
        seed: int = 42,
    ):

        if initial_capital <= 0:
            raise ValueError(
                "initial_capital must be > 0"
            )

        if not 0 < risk_percent <= 1:
            raise ValueError(
                "risk_percent must be between 0 and 1"
            )

        self.initial_capital = (
            initial_capital
        )

        self.risk_percent = (
            risk_percent
        )

        self.seed = seed

    def run(
        self,
        realized_r: list[float],
        simulations: int = 5000,
    ) -> MonteCarloResult:

        if not realized_r:
            raise ValueError(
                "No trade outcomes"
            )

        if simulations <= 0:
            raise ValueError(
                "simulations must be > 0"
            )

        rng = random.Random(
            self.seed
        )

        final_equities = []
        max_drawdowns = []

        for _ in range(simulations):

            sequence = [
                rng.choice(realized_r)
                for _ in range(
                    len(realized_r)
                )
            ]

            equity = (
                self.initial_capital
            )

            peak = equity
            max_dd = 0.0

            for r in sequence:

                risk_amount = (
                    equity
                    * self.risk_percent
                )

                pnl = (
                    r * risk_amount
                )

                equity += pnl

                if equity > peak:
                    peak = equity

                drawdown = (
                    (peak - equity)
                    / peak
                    if peak > 0
                    else 0.0
                )

                max_dd = max(
                    max_dd,
                    drawdown,
                )

            final_equities.append(
                equity
            )

            max_drawdowns.append(
                max_dd
            )

        final_equities.sort()
        max_drawdowns.sort()

        return MonteCarloResult(
            simulations=simulations,

            median_final_equity=(
                self._percentile(
                    final_equities,
                    50,
                )
            ),

            worst_final_equity=(
                final_equities[0]
            ),

            best_final_equity=(
                final_equities[-1]
            ),

            median_max_drawdown=(
                self._percentile(
                    max_drawdowns,
                    50,
                )
            ),

            worst_max_drawdown=(
                max_drawdowns[-1]
            ),

            probability_dd_5pct=(
                self._probability_above(
                    max_drawdowns,
                    0.05,
                )
            ),

            probability_dd_10pct=(
                self._probability_above(
                    max_drawdowns,
                    0.10,
                )
            ),

            probability_dd_20pct=(
                self._probability_above(
                    max_drawdowns,
                    0.20,
                )
            ),
        )

    @staticmethod
    def _percentile(
        values: list[float],
        percentile: float,
    ) -> float:

        if not values:
            return 0.0

        index = (
            (len(values) - 1)
            * percentile
            / 100.0
        )

        lower = int(index)
        upper = min(
            lower + 1,
            len(values) - 1,
        )

        weight = index - lower

        return (
            values[lower]
            * (1.0 - weight)
            + values[upper]
            * weight
        )

    @staticmethod
    def _probability_above(
        values: list[float],
        threshold: float,
    ) -> float:

        if not values:
            return 0.0

        count = sum(
            value >= threshold
            for value in values
        )

        return count / len(values)
