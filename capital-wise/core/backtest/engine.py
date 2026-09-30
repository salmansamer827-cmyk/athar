from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from core.backtest.outcome import (
    TradeOutcomeEngine,
    OutcomeStatus,
)
from core.backtest.models import (
    BacktestTrade,
    TradeOutcome,
)


@dataclass(frozen=True)
class BacktestConfig:
    risk_percent: float = 0.01
    reward_risk: float = 3.0

    profile_lookback: int = 100
    forward_bars: int = 100

    min_probability: float = 0.55
    min_ev_r: float = 0.0

    allow_long: bool = True
    allow_short: bool = True


class HistoricalBacktestEngine:
    """
    CAPITAL WISE
    Historical Quantitative Backtest Engine

    البيانات المستخدمة لاتخاذ القرار يجب أن تكون
    متاحة قبل لحظة الدخول فقط.
    """

    def __init__(
        self,
        config: BacktestConfig | None = None,
    ):
        self.config = (
            config
            if config is not None
            else BacktestConfig()
        )

        self.outcome_engine = (
            TradeOutcomeEngine()
        )

    def run(
        self,
        candles: list[dict],
        signal_function: Callable[
            [list[dict]],
            Optional[dict],
        ],
    ) -> list[BacktestTrade]:

        if not candles:
            raise ValueError(
                "candles cannot be empty"
            )

        if len(candles) < (
            self.config.profile_lookback
            + self.config.forward_bars
            + 1
        ):
            raise ValueError(
                "Not enough candles"
            )

        trades: list[BacktestTrade] = []

        i = self.config.profile_lookback

        while i < (
            len(candles)
            - self.config.forward_bars
        ):

            history = candles[
                i - self.config.profile_lookback:i
            ]

            signal = signal_function(
                history
            )

            if signal is None:
                i += 1
                continue

            direction = signal.get(
                "direction"
            )

            probability = float(
                signal.get(
                    "probability",
                    0.0,
                )
            )

            ev_r = float(
                signal.get(
                    "ev_r",
                    0.0,
                )
            )

            entry = float(
                signal.get(
                    "entry",
                    candles[i]["close"],
                )
            )

            stop_loss = float(
                signal["stop_loss"]
            )

            take_profit = float(
                signal["take_profit"]
            )

            if probability < (
                self.config.min_probability
            ):
                i += 1
                continue

            if ev_r <= (
                self.config.min_ev_r
            ):
                i += 1
                continue

            if direction == "LONG":

                if not self.config.allow_long:
                    i += 1
                    continue

            elif direction == "SHORT":

                if not self.config.allow_short:
                    i += 1
                    continue

            else:
                i += 1
                continue

            future = candles[
                i + 1:
                i + 1 + self.config.forward_bars
            ]

            outcome = (
                self.outcome_engine.evaluate(
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    candles=future,
                    direction=direction,
                )
            )

            if outcome.status == (
                OutcomeStatus.OPEN
            ):
                i += 1
                continue

            if outcome.status == (
                OutcomeStatus.AMBIGUOUS
            ):
                i += 1
                continue

            trades.append(
                BacktestTrade(
                    timestamp=candles[i]["timestamp"],

                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,

                    risk_r=1.0,
                    reward_r=self.config.reward_risk,

                    outcome=TradeOutcome(
                        outcome.status.value
                    ),

                    realized_r=(
                        outcome.realized_r
                    ),

                    market_state=str(
                        signal.get(
                            "market_state",
                            "UNKNOWN",
                        )
                    ),

                    probability=probability,

                    transaction_cost_r=float(
                        signal.get(
                            "transaction_cost_r",
                            0.0,
                        )
                    ),
                )
            )

            # لا نفتح صفقة جديدة أثناء
            # الصفقة الحالية.
            if outcome.bars_held:
                i += outcome.bars_held + 1
            else:
                i += 1

        return trades
