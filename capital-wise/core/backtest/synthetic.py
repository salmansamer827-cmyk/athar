from __future__ import annotations

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class SyntheticConfig:
    candles: int = 500
    start_price: float = 100.0
    seed: int = 42

    trend_strength: float = 0.0008
    volatility: float = 0.006

    regime_length: int = 80


class SyntheticMarketGenerator:
    """
    CAPITAL WISE
    Synthetic Quantitative Market Generator

    Generates multiple market regimes:

    TREND_UP
    RANGE
    TREND_DOWN
    HIGH_VOLATILITY
    LOW_VOLATILITY
    """

    def __init__(
        self,
        config: SyntheticConfig | None = None,
    ):
        self.config = (
            config
            if config is not None
            else SyntheticConfig()
        )

        self.rng = random.Random(
            self.config.seed
        )

    def generate(self) -> list[dict]:

        price = self.config.start_price

        candles: list[dict] = []

        regimes = [
            "TREND_UP",
            "RANGE",
            "TREND_DOWN",
            "HIGH_VOLATILITY",
            "LOW_VOLATILITY",
        ]

        for i in range(
            self.config.candles
        ):

            regime_index = (
                i // self.config.regime_length
            ) % len(regimes)

            regime = regimes[
                regime_index
            ]

            drift, volatility = (
                self._regime_parameters(
                    regime
                )
            )

            previous = price

            shock = self.rng.gauss(
                0.0,
                volatility
            )

            return_pct = (
                drift + shock
            )

            price = max(
                0.000001,
                previous
                * (1.0 + return_pct)
            )

            spread = abs(
                price
                * volatility
                * self.rng.uniform(
                    0.5,
                    1.5,
                )
            )

            open_price = previous

            close_price = price

            high = max(
                open_price,
                close_price,
            ) + spread

            low = min(
                open_price,
                close_price,
            ) - spread

            volume = (
                self.rng.lognormvariate(
                    math.log(1000.0),
                    0.35,
                )
            )

            candles.append(
                {
                    "timestamp": i,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "volume": volume,
                    "regime": regime,
                }
            )

        return candles

    def _regime_parameters(
        self,
        regime: str,
    ) -> tuple[float, float]:

        base_vol = (
            self.config.volatility
        )

        trend = (
            self.config.trend_strength
        )

        if regime == "TREND_UP":
            return (
                trend,
                base_vol,
            )

        if regime == "TREND_DOWN":
            return (
                -trend,
                base_vol,
            )

        if regime == "HIGH_VOLATILITY":
            return (
                0.0,
                base_vol * 2.5,
            )

        if regime == "LOW_VOLATILITY":
            return (
                0.0,
                base_vol * 0.35,
            )

        # RANGE
        return (
            0.0,
            base_vol * 0.7,
        )
