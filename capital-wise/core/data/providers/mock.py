from __future__ import annotations

from core.data.models import OHLCV
from core.data.router import (
    MarketDataProvider,
)


class MockMarketProvider(
    MarketDataProvider
):
    """
    Deterministic provider used for
    architecture and unit testing.
    """

    def __init__(
        self,
        market: str,
    ):
        self.market = market.upper()

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[OHLCV]:

        candles = []

        price = 100.0

        for i in range(limit):

            open_price = price

            close_price = (
                price + 0.10
            )

            high = (
                close_price + 0.20
            )

            low = (
                open_price - 0.20
            )

            candles.append(
                OHLCV(
                    timestamp=(
                        1_000_000 + i
                    ),

                    open=open_price,
                    high=high,
                    low=low,
                    close=close_price,

                    volume=1000.0,

                    symbol=symbol,
                    market=self.market,
                    timeframe=timeframe,
                )
            )

            price = close_price

        return candles
