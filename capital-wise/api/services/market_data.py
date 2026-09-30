from __future__ import annotations

from api.services.binance_data import BinanceDataService


class MarketDataService:
    """
    CAPITAL WISE

    Unified market-data service.

    Binance is the primary live market-data provider.
    No CCXT dependency.
    """

    def __init__(self):
        self.binance = BinanceDataService()

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 200,
        market: str = "CRYPTO",
    ):
        return self.binance.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            market=market,
        )
