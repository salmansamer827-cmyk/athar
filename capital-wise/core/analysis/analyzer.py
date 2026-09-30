from __future__ import annotations

from dataclasses import dataclass

from core.data.models import OHLCV


@dataclass(frozen=True)
class AnalysisInput:
    symbol: str
    market: str
    timeframe: str

    candles: list[OHLCV]


@dataclass(frozen=True)
class PriceStatistics:
    minimum: float
    maximum: float
    mean: float
    standard_deviation: float


class QuantAnalyzer:
    """
    CAPITAL WISE

    Central quantitative analysis entry point.

    This layer intentionally does not contain
    trading logic. It prepares validated market
    data for the quantitative engines.
    """

    def analyze_prices(
        self,
        candles: list[OHLCV],
    ) -> PriceStatistics:

        if not candles:
            raise ValueError(
                "No candles supplied"
            )

        prices = [
            candle.close
            for candle in candles
        ]

        mean = (
            sum(prices)
            / len(prices)
        )

        variance = (
            sum(
                (price - mean) ** 2
                for price in prices
            )
            / len(prices)
        )

        std = variance ** 0.5

        return PriceStatistics(
            minimum=min(prices),
            maximum=max(prices),
            mean=mean,
            standard_deviation=std,
        )
