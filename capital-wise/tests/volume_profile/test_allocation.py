import numpy as np

from core.volume_profile.quant.allocation import (
    allocate_candle_volume,
)


bin_edges = np.arange(
    90,
    111,
    1,
    dtype=float,
)


candles = [
    {
        "low": 92.0,
        "high": 97.0,
        "volume": 1000.0,
    },
    {
        "low": 95.5,
        "high": 103.5,
        "volume": 2500.0,
    },
    {
        "low": 101.0,
        "high": 108.0,
        "volume": 1500.0,
    },
]


print("=" * 60)
print("CAPITAL WISE")
print("VOLUME ALLOCATION ENGINE")
print("=" * 60)

original_total = 0.0
allocated_total = 0.0


for number, candle in enumerate(
    candles,
    start=1,
):

    distribution = allocate_candle_volume(
        low=candle["low"],
        high=candle["high"],
        volume=candle["volume"],
        bin_edges=bin_edges,
    )

    original = candle["volume"]
    allocated = float(
        distribution.sum()
    )

    original_total += original
    allocated_total += allocated

    error = abs(
        allocated - original
    )

    print()
    print(f"Candle {number}")
    print(f"Original Volume:  {original:.10f}")
    print(f"Allocated Volume: {allocated:.10f}")
    print(f"Error:            {error:.12f}")


total_error = abs(
    allocated_total - original_total
)

relative_error = (
    total_error / original_total
)


print()
print("-" * 60)
print(
    f"Original Total:   "
    f"{original_total:.10f}"
)

print(
    f"Allocated Total:  "
    f"{allocated_total:.10f}"
)

print(
    f"Absolute Error:   "
    f"{total_error:.12f}"
)

print(
    f"Relative Error:   "
    f"{relative_error:.12e}"
)

print("=" * 60)
