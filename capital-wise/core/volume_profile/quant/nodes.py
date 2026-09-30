from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class VolumeNode:
    kind: str
    lower_price: float
    upper_price: float
    center_price: float

    peak_volume: float
    total_volume: float

    relative_strength: float
    density: float
    width: float


def _validate_inputs(
    prices: np.ndarray,
    volume: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:

    prices = np.asarray(
        prices,
        dtype=np.float64,
    )

    volume = np.asarray(
        volume,
        dtype=np.float64,
    )

    if prices.ndim != 1 or volume.ndim != 1:
        raise ValueError(
            "prices and volume must be one-dimensional"
        )

    if len(prices) != len(volume):
        raise ValueError(
            "prices and volume must have equal length"
        )

    if len(prices) < 3:
        raise ValueError(
            "at least 3 bins are required"
        )

    if np.any(volume < 0):
        raise ValueError(
            "volume cannot be negative"
        )

    return prices, volume


def detect_volume_nodes(
    prices: np.ndarray,
    volume: np.ndarray,
    hvn_zscore: float = 0.75,
    lvn_zscore: float = -0.75,
) -> tuple[list[VolumeNode], list[VolumeNode]]:

    prices, volume = _validate_inputs(
        prices,
        volume,
    )

    median_volume = float(
        np.median(volume)
    )

    mean_volume = float(
        np.mean(volume)
    )

    std_volume = float(
        np.std(volume)
    )

    if std_volume <= 0:
        return [], []

    hvn_threshold = (
        mean_volume
        + hvn_zscore * std_volume
    )

    lvn_threshold = (
        mean_volume
        + lvn_zscore * std_volume
    )

    hvn_indices = []
    lvn_indices = []

    for i in range(1, len(volume) - 1):

        is_peak = (
            volume[i] > volume[i - 1]
            and volume[i] >= volume[i + 1]
        )

        is_valley = (
            volume[i] < volume[i - 1]
            and volume[i] <= volume[i + 1]
        )

        if is_peak and volume[i] >= hvn_threshold:
            hvn_indices.append(i)

        if is_valley and volume[i] <= lvn_threshold:
            lvn_indices.append(i)

    bin_widths = np.diff(prices)

    default_width = float(
        np.median(bin_widths)
    )

    hvn_nodes = _build_nodes(
        "HVN",
        hvn_indices,
        prices,
        volume,
        median_volume,
        default_width,
    )

    lvn_nodes = _build_nodes(
        "LVN",
        lvn_indices,
        prices,
        volume,
        median_volume,
        default_width,
    )

    return hvn_nodes, lvn_nodes


def _build_nodes(
    kind: str,
    indices: list[int],
    prices: np.ndarray,
    volume: np.ndarray,
    median_volume: float,
    bin_width: float,
) -> list[VolumeNode]:

    nodes = []

    for index in indices:

        peak_volume = float(
            volume[index]
        )

        relative_strength = (
            peak_volume / median_volume
            if median_volume > 0
            else 0.0
        )

        lower_price = float(
            prices[index] - bin_width / 2
        )

        upper_price = float(
            prices[index] + bin_width / 2
        )

        total_volume = peak_volume

        density = (
            peak_volume / bin_width
            if bin_width > 0
            else 0.0
        )

        nodes.append(
            VolumeNode(
                kind=kind,
                lower_price=lower_price,
                upper_price=upper_price,
                center_price=float(
                    prices[index]
                ),
                peak_volume=peak_volume,
                total_volume=total_volume,
                relative_strength=relative_strength,
                density=density,
                width=bin_width,
            )
        )

    return nodes
