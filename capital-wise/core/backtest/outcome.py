from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OutcomeStatus(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    AMBIGUOUS = "AMBIGUOUS"
    OPEN = "OPEN"


@dataclass(frozen=True)
class OutcomeResult:
    status: OutcomeStatus
    realized_r: float
    exit_price: float | None
    bars_held: int | None


class TradeOutcomeEngine:

    def evaluate(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float,
        candles: list[dict],
        direction: str = "LONG",
    ) -> OutcomeResult:

        if entry <= 0:
            raise ValueError(
                "entry must be > 0"
            )

        if direction not in {
            "LONG",
            "SHORT",
        }:
            raise ValueError(
                "direction must be LONG or SHORT"
            )

        if direction == "LONG":

            if not (
                stop_loss < entry < take_profit
            ):
                raise ValueError(
                    "Invalid LONG levels"
                )

        else:

            if not (
                take_profit < entry < stop_loss
            ):
                raise ValueError(
                    "Invalid SHORT levels"
                )

        price_risk = abs(
            entry - stop_loss
        )

        for index, candle in enumerate(
            candles,
            start=1,
        ):

            high = float(candle["high"])
            low = float(candle["low"])

            if direction == "LONG":

                hit_sl = (
                    low <= stop_loss
                )

                hit_tp = (
                    high >= take_profit
                )

                if hit_sl and hit_tp:
                    return OutcomeResult(
                        status=OutcomeStatus.AMBIGUOUS,
                        realized_r=0.0,
                        exit_price=None,
                        bars_held=index,
                    )

                if hit_sl:

                    return OutcomeResult(
                        status=OutcomeStatus.LOSS,
                        realized_r=-1.0,
                        exit_price=stop_loss,
                        bars_held=index,
                    )

                if hit_tp:

                    return OutcomeResult(
                        status=OutcomeStatus.WIN,
                        realized_r=(
                            abs(
                                take_profit
                                - entry
                            )
                            / price_risk
                        ),
                        exit_price=take_profit,
                        bars_held=index,
                    )

            else:

                hit_sl = (
                    high >= stop_loss
                )

                hit_tp = (
                    low <= take_profit
                )

                if hit_sl and hit_tp:
                    return OutcomeResult(
                        status=OutcomeStatus.AMBIGUOUS,
                        realized_r=0.0,
                        exit_price=None,
                        bars_held=index,
                    )

                if hit_sl:

                    return OutcomeResult(
                        status=OutcomeStatus.LOSS,
                        realized_r=-1.0,
                        exit_price=stop_loss,
                        bars_held=index,
                    )

                if hit_tp:

                    return OutcomeResult(
                        status=OutcomeStatus.WIN,
                        realized_r=(
                            abs(
                                take_profit
                                - entry
                            )
                            / price_risk
                        ),
                        exit_price=take_profit,
                        bars_held=index,
                    )

        return OutcomeResult(
            status=OutcomeStatus.OPEN,
            realized_r=0.0,
            exit_price=None,
            bars_held=None,
        )
