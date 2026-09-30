import numpy as np

from core.volume_profile.quant.distribution import (
    normalize_volume,
    volume_entropy,
    normalized_entropy,
)

from core.volume_profile.quant.statistics import (
    weighted_mean,
    weighted_variance,
    weighted_std,
    weighted_skewness,
    weighted_kurtosis,
)


prices = np.array(
    [90, 95, 100, 105, 110],
    dtype=float,
)

volume = np.array(
    [100, 200, 500, 200, 100],
    dtype=float,
)


probability = normalize_volume(volume)

print("=" * 60)
print("CAPITAL WISE")
print("QUANTITATIVE VOLUME PROFILE TEST")
print("=" * 60)

print("Probability Distribution:")
print(probability)

print()
print("Probability Sum:")
print(probability.sum())

print()
print("Entropy:")
print(volume_entropy(volume))

print()
print("Normalized Entropy:")
print(normalized_entropy(volume))

print()
print("Weighted Mean:")
print(weighted_mean(prices, volume))

print()
print("Weighted Variance:")
print(weighted_variance(prices, volume))

print()
print("Weighted Std:")
print(weighted_std(prices, volume))

print()
print("Weighted Skewness:")
print(weighted_skewness(prices, volume))

print()
print("Weighted Kurtosis:")
print(weighted_kurtosis(prices, volume))

print("=" * 60)
