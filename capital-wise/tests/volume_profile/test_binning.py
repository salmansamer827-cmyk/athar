from core.volume_profile.quant.binning import (
    AdaptiveBinning,
)


engine = AdaptiveBinning(
    min_bins=40,
    max_bins=300,
)


tests = [
    {
        "name": "BTC",
        "low": 95000,
        "high": 105000,
        "observations": 1000,
        "tick": 0.10,
    },
    {
        "name": "STOCK",
        "low": 90,
        "high": 110,
        "observations": 1000,
        "tick": 0.01,
    },
    {
        "name": "LOW SAMPLE",
        "low": 100,
        "high": 110,
        "observations": 100,
        "tick": 0.01,
    },
]


print("=" * 60)
print("CAPITAL WISE")
print("ADAPTIVE BINNING ENGINE")
print("=" * 60)


for item in tests:

    result = engine.calculate(
        price_low=item["low"],
        price_high=item["high"],
        observations=item["observations"],
        tick_size=item["tick"],
    )

    print()
    print(item["name"])
    print(f"Bins:      {result.bins}")
    print(f"Low:       {result.price_low}")
    print(f"High:      {result.price_high}")
    print(f"Bin Size:  {result.bin_size}")


print()
print("=" * 60)
