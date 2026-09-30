from core.backtest.synthetic import (
    SyntheticMarketGenerator,
    SyntheticConfig,
)


generator = SyntheticMarketGenerator(
    SyntheticConfig(
        candles=500,
        start_price=100.0,
        seed=42,
    )
)

candles = generator.generate()


print("=" * 60)
print("CAPITAL WISE")
print("SYNTHETIC MARKET GENERATOR")
print("=" * 60)

print(
    f"Candles: {len(candles)}"
)

regimes = {}

for candle in candles:

    regime = candle["regime"]

    regimes[regime] = (
        regimes.get(regime, 0) + 1
    )

for regime, count in regimes.items():

    print(
        f"{regime:<20}"
        f"{count}"
    )

print("-" * 60)

print(
    f"First Price: "
    f"{candles[0]['close']:.6f}"
)

print(
    f"Last Price:  "
    f"{candles[-1]['close']:.6f}"
)

print(
    f"Min Price:   "
    f"{min(c['low'] for c in candles):.6f}"
)

print(
    f"Max Price:   "
    f"{max(c['high'] for c in candles):.6f}"
)

print("=" * 60)
