from __future__ import annotations

import numpy as np


def weighted_mean(
    prices: np.ndarray,
    volume: np.ndarray,
) -> float:

    prices = np.asarray(
        prices,
        dtype=np.float64,
    )

    volume = np.asarray(
        volume,
        dtype=np.float64,
    )

    total = volume.sum()

    if total <= 0:
        raise ValueError(
            "volume must be > 0"
        )

    return float(
        np.sum(prices * volume)
        / total
    )


def weighted_variance(
    prices: np.ndarray,
    volume: np.ndarray,
) -> float:

    mean = weighted_mean(
        prices,
        volume,
    )

    total = volume.sum()

    return float(
        np.sum(
            volume
            * (prices - mean) ** 2
        )
        / total
    )


def weighted_std(
    prices: np.ndarray,
    volume: np.ndarray,
) -> float:

    return float(
        np.sqrt(
            weighted_variance(
                prices,
                volume,
            )
        )
    )


def weighted_skewness(
    prices: np.ndarray,
    volume: np.ndarray,
) -> float:

    mean = weighted_mean(
        prices,
        volume,
    )

    std = weighted_std(
        prices,
        volume,
    )

    if std <= 0:
        return 0.0

    total = volume.sum()

    return float(
        np.sum(
            volume
            * ((prices - mean) / std) ** 3
        )
        / total
    )


def weighted_kurtosis(
    prices: np.ndarray,
    volume: np.ndarray,
) -> float:

    mean = weighted_mean(
        prices,
        volume,
    )

    std = weighted_std(
        prices,
        volume,
    )

    if std <= 0:
        return 0.0

    total = volume.sum()

    return float(
        np.sum(
            volume
            * ((prices - mean) / std) ** 4
        )
        / total
    )
