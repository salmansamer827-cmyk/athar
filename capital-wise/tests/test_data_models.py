from core.data.models import (
    OHLCV,
    MarketInfo,
)


candle = OHLCV(
    timestamp=1755000000000,

    open=100.0,
    high=105.0,
    low=98.0,
    close=103.0,

    volume=1500.0,

    symbol="BTC/USDT",
    market="CRYPTO",
    timeframe="15m",
)


market = MarketInfo(
    market="CRYPTO",
    symbol="BTC/USDT",

    tick_size=0.1,
    contract_size=1.0,

    leverage_available=True,

    quote_currency="USDT",
    base_currency="BTC",
)


print("=" * 60)
print("CAPITAL WISE")
print("NORMALIZED MARKET DATA MODEL")
print("=" * 60)

print(
    f"Market:          {candle.market}"
)

print(
    f"Symbol:          {candle.symbol}"
)

print(
    f"Timeframe:       {candle.timeframe}"
)

print(
    f"Open:            {candle.open}"
)

print(
    f"High:            {candle.high}"
)

print(
    f"Low:             {candle.low}"
)

print(
    f"Close:           {candle.close}"
)

print(
    f"Volume:          {candle.volume}"
)

print(
    f"Typical Price:   "
    f"{candle.typical_price:.6f}"
)

print(
    f"Range:           "
    f"{candle.price_range:.6f}"
)

print(
    f"Body:            "
    f"{candle.body:.6f}"
)

print(
    f"Bullish:         "
    f"{candle.bullish}"
)

print(
    f"Bearish:         "
    f"{candle.bearish}"
)

print("-" * 60)

print(
    f"Tick Size:       "
    f"{market.tick_size}"
)

print(
    f"Contract Size:   "
    f"{market.contract_size}"
)

print(
    f"Leverage:        "
    f"{market.leverage_available}"
)

print("=" * 60)
