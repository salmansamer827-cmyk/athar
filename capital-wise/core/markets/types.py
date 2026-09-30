from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MarketType(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCKS = "stocks"
    FUTURES = "futures"


@dataclass(frozen=True)
class MarketSpec:
    market: MarketType

    symbol: str
    timeframe: str

    tick_size: float
    contract_size: float

    leverage_allowed: bool

    min_position_size: float
    max_position_size: float


MARKET_DEFAULTS = {
    MarketType.CRYPTO: {
        "contract_size": 1.0,
        "leverage_allowed": True,
    },

    MarketType.FOREX: {
        "contract_size": 100000.0,
        "leverage_allowed": True,
    },

    MarketType.STOCKS: {
        "contract_size": 1.0,
        "leverage_allowed": False,
    },

    MarketType.FUTURES: {
        "contract_size": 1.0,
        "leverage_allowed": True,
    },
}


def create_market_spec(
    market: MarketType,
    symbol: str,
    timeframe: str,
    tick_size: float,
    min_position_size: float = 0.0,
    max_position_size: float = float("inf"),
) -> MarketSpec:

    if tick_size <= 0:
        raise ValueError(
            "tick_size must be > 0"
        )

    defaults = MARKET_DEFAULTS[market]

    return MarketSpec(
        market=market,
        symbol=symbol,
        timeframe=timeframe,
        tick_size=tick_size,
        contract_size=defaults["contract_size"],
        leverage_allowed=defaults["leverage_allowed"],
        min_position_size=min_position_size,
        max_position_size=max_position_size,
    )
