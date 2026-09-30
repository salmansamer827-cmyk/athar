import numpy as np
import pandas as pd

from core.volume_profile.engine import (
    MathematicalVolumeProfile,
)


np.random.seed(42)

n = 1000

price = 100 + np.cumsum(
    np.random.normal(0, 0.5, n)
)

df = pd.DataFrame({
    "high": price + np.random.uniform(0.1, 0.5, n),
    "low": price - np.random.uniform(0.1, 0.5, n),
    "close": price,
    "volume": np.random.uniform(100, 1000, n),
})


engine = MathematicalVolumeProfile(
    bins=120,
    value_area=0.70,
)

result = engine.calculate(df)


print()
print("=" * 60)
print("CAPITAL WISE")
print("MATHEMATICAL VOLUME PROFILE")
print("=" * 60)

print(f"POC: {result.poc:.6f}")
print(f"VAH: {result.vah:.6f}")
print(f"VAL: {result.val:.6f}")

print(
    f"Total Volume: "
    f"{result.total_volume:.2f}"
)

print(
    f"Value Area Volume: "
    f"{result.value_area_volume:.2f}"
)

print(
    f"Value Area %: "
    f"{result.value_area_percentage * 100:.2f}%"
)

print(
    f"Bin Size: "
    f"{result.bin_size:.6f}"
)

print()
print("HVN:")
print(result.hvn)

print()
print("LVN:")
print(result.lvn)

print("=" * 60)
