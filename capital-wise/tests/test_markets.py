from core.markets.types import (
    MarketType,
    create_market_spec,
)


markets = [
    create_market_spec(
        MarketType.CRYPTO,
        "BTC/USDT",
        "15m",
        0.10,
    ),

    create_market_spec(
        MarketType.FOREX,
        "EUR/USD",
        "15m",
        0.00001,
    ),

    create_market_spec(
        MarketType.STOCKS,
        "AAPL",
        "15m",
        0.01,
    ),

    create_market_spec(
        MarketType.FUTURES,
        "ES",
        "15m",
        0.25,
    ),
]


print("=" * 60)
print("CAPITAL WISE")
print("MULTI-MARKET QUANT ENGINE")
print("=" * 60)

for market in markets:

    print()
    print(
        f"Market:       "
        f"{market.market.value.upper()}"
    )

    print(
        f"Symbol:       "
        f"{market.symbol}"
    )

    print(
        f"Timeframe:    "
        f"{market.timeframe}"
    )

    print(
        f"Tick Size:    "
        f"{market.tick_size}"
    )

    print(
        f"Contract:     "
        f"{market.contract_size}"
    )

    print(
        f"Leverage:     "
        f"{market.leverage_allowed}"
    )

print()
print("=" * 60)
