from core.data.router import (
    MarketDataRouter,
)

from core.data.providers.mock import (
    MockMarketProvider,
)


router = MarketDataRouter()


markets = {
    "CRYPTO": "BTC/USDT",
    "FOREX": "EUR/USD",
    "STOCKS": "AAPL",
    "FUTURES": "ES",
}


for market in markets:

    router.register(
        MockMarketProvider(
            market
        )
    )


print("=" * 60)
print("CAPITAL WISE")
print("MULTI-MARKET DATA ROUTER")
print("=" * 60)


for market, symbol in markets.items():

    candles = router.fetch(
        market=market,
        symbol=symbol,
        timeframe="15m",
        limit=10,
    )

    first = candles[0]

    print()
    print(
        f"Market:       {market}"
    )

    print(
        f"Symbol:       {symbol}"
    )

    print(
        f"Candles:      {len(candles)}"
    )

    print(
        f"First Close:  "
        f"{first.close:.4f}"
    )

    print(
        f"Total Volume: "
        f"{sum(c.volume for c in candles):.2f}"
    )


print()
print("=" * 60)
