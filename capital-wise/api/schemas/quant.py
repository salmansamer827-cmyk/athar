from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field


class CandleInput(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    market: str
    timeframe: str


class QuantAnalyzeRequest(BaseModel):
    symbol: str
    market: str = "CRYPTO"
    timeframe: str

    candles: Optional[List[CandleInput]] = None

    capital: float = Field(default=100.0, gt=0)

    entry: Optional[float] = None
    stop_price: Optional[float] = None
    tick_size: Optional[float] = None

    wins: int = Field(default=72, ge=0)
    losses: int = Field(default=28, ge=0)

    limit: int = Field(default=100, ge=2, le=1000)
