from __future__ import annotations

import numpy as np


def allocate_candle_volume(
    low: float,
    high: float,
    volume: float,
    bin_edges: np.ndarray,
) -> np.ndarray:

    if high < low:
        raise ValueError("high must be >= low")

    if low <= 0:
        raise ValueError("low must be > 0")

    if volume < 0:
        raise ValueError("volume cannot be negative")

    edges = np.asarray(
        bin_edges,
        dtype=np.float64,
    )

    if edges.ndim != 1 or len(edges) < 2:
        raise ValueError(
            "bin_edges must contain at least 2 values"
        )

    if np.any(np.diff(edges) <= 0):
        raise ValueError(
            "bin_edges must be strictly increasing"
        )

    result = np.zeros(
        len(edges) - 1,
        dtype=np.float64,
    )

    if volume == 0:
        return result

    # شمعة بدون range
    if high == low:

        index = np.searchsorted(
            edges,
            low,
            side="right",
        ) - 1

        index = max(
            0,
            min(index, len(result) - 1),
        )

        result[index] = volume

        return result

    candle_range = high - low

    for i in range(len(result)):

        bin_low = edges[i]
        bin_high = edges[i + 1]

        overlap = max(
            0.0,
            min(high, bin_high)
            - max(low, bin_low),
        )

        if overlap > 0:

            fraction = (
                overlap / candle_range
            )

            result[i] = (
                volume * fraction
            )

    # تصحيح floating-point حتى لا نفقد الحجم.
    allocated = result.sum()

    if allocated > 0:

        result *= (
            volume / allocated
        )

    return result
