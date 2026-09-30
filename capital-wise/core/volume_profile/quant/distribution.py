from __future__ import annotations

import numpy as np


def normalize_volume(
    volume: np.ndarray,
) -> np.ndarray:
    """
    تحويل توزيع الحجم إلى Probability Distribution.
    """

    volume = np.asarray(
        volume,
        dtype=np.float64,
    )

    if volume.ndim != 1:
        raise ValueError(
            "volume must be one-dimensional"
        )

    if np.any(volume < 0):
        raise ValueError(
            "volume cannot contain negative values"
        )

    total = float(volume.sum())

    if total <= 0:
        raise ValueError(
            "total volume must be > 0"
        )

    return volume / total


def volume_entropy(
    volume: np.ndarray,
) -> float:
    """
    Shannon entropy لتوزيع الحجم.
    """

    probability = normalize_volume(volume)

    non_zero = probability[
        probability > 0
    ]

    return float(
        -np.sum(
            non_zero * np.log(non_zero)
        )
    )


def normalized_entropy(
    volume: np.ndarray,
) -> float:
    """
    Entropy normalized إلى [0, 1].
    """

    probability = normalize_volume(volume)

    n = len(probability)

    if n <= 1:
        return 0.0

    entropy = volume_entropy(volume)

    return float(
        entropy / np.log(n)
    )
