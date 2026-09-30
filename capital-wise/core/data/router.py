from __future__ import annotations

from abc import ABC, abstractmethod

from core.data.models import OHLCV
from core.data.quality import DataQualityEngine


SUPPORTED_MARKETS = {
    "CRYPTO",
    "FOREX",
    "STOCKS",
    "FUTURES",
}


class MarketDataProvider(ABC):
    """
    Common interface for every market-data provider.
    """

    market: str

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[OHLCV]:
        raise NotImplementedError


class MarketDataRouter:
    """
    CAPITAL WISE

    Unified market-data routing layer.

    Provider -> OHLCV -> Quality -> Quant Engine
    """

    def __init__(self):
        self.providers: dict[
            str,
            MarketDataProvider,
        ] = {}

        self.quality = DataQualityEngine()

    def register(
        self,
        provider: MarketDataProvider,
    ) -> None:

        market = provider.market.upper()

        if market not in SUPPORTED_MARKETS:
            raise ValueError(
                f"Unsupported market: {market}"
            )

        self.providers[market] = provider

    def fetch(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[OHLCV]:

        market = market.upper()

        if market not in SUPPORTED_MARKETS:
            raise ValueError(
                f"Unsupported market: {market}"
            )

        if market not in self.providers:
            raise RuntimeError(
                f"No provider registered for {market}"
            )

        candles = self.providers[
            market
        ].fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        report = self.quality.validate(
            candles
        )

        if not report.valid:
            raise ValueError(
                "Market data failed "
                f"quality validation: "
                f"{report.errors}"
            )

        return candles
