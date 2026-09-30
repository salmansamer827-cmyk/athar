from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class OHLCV:
    """
    CAPITAL WISE
    Normalized Market Candle

    Standard representation used by all
    market-data providers.
    """

    timestamp: int

    open: float
    high: float
    low: float
    close: float

    volume: float

    symbol: str
    market: str
    timeframe: str

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(
            self.timestamp / 1000.0
        )

    @property
    def typical_price(self) -> float:
        """
        Typical Price:

        TP = (High + Low + Close) / 3
        """
        return (
            self.high
            + self.low
            + self.close
        ) / 3.0

    @property
    def price_range(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(
            self.close - self.open
        )

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open


@dataclass(frozen=True)
class MarketInfo:
    """
    CAPITAL WISE
    Market Specification
    """

    market: str
    symbol: str

    tick_size: float
    contract_size: float

    leverage_available: bool

    quote_currency: Optional[str] = None
    base_currency: Optional[str] = None
