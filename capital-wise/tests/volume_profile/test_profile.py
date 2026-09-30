import numpy as np
import pandas as pd

from core.volume_profile.quant.profile import (
    QuantProfileEngine,
)


np.random.seed(42)

n = 500

close = np.cumsum(
    np.random.normal(
        0,
        1,
        n,
    )
) + 100

high = (
    close
    + np.random.uniform(
        0.1,
        1.5,
        n,
    )
)

low = (
    close
    - np.random.uniform(
        0.1,
        1.5,
        n,
    )
)

volume = np.random.uniform(
    100,
    1000,
    n,
)


df = pd.DataFrame({
    "high": high,
    "low": low,
    "close": close,
    "volume": volume,
})


engine = QuantProfileEngine(
    value_area=0.70,
    min_bins=40,
    max_bins=120,
)


profile = engine.calculate(
    df,
    tick_size=0.01,
)


print("=" * 60)
print("CAPITAL WISE")
print("QUANT PROFILE ENGINE")
print("=" * 60)

print(f"Price Low:          {profile.price_low:.6f}")
print(f"Price High:         {profile.price_high:.6f}")

print(f"Bins:               {profile.bins}")
print(f"Bin Size:           {profile.bin_size:.6f}")

print(f"Total Volume:       {profile.total_volume:.6f}")

print()
print(f"POC:                {profile.poc:.6f}")
print(f"VAH:                {profile.vah:.6f}")
print(f"VAL:                {profile.val:.6f}")

print()
print(f"Weighted Mean:      {profile.weighted_mean:.6f}")
print(f"Variance:           {profile.variance:.6f}")
print(f"Std:                {profile.std:.6f}")
print(f"Skewness:           {profile.skewness:.6f}")
print(f"Kurtosis:           {profile.kurtosis:.6f}")

print()
print(f"Entropy:            {profile.entropy:.6f}")
print(
    f"Concentration:      "
    f"{profile.volume_concentration:.6f}"
)

print()
print(
    "Probability Sum:   "
    f"{profile.probability_distribution.sum():.12f}"
)

print(
    "Profile Volume:    "
    f"{profile.volume_distribution.sum():.6f}"
)

print("=" * 60)
