from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class VolumeProfileResult:
    poc: float
    vah: float
    val: float
    hvn: list[float]
    lvn: list[float]
    total_volume: float
    value_area_volume: float
    value_area_percentage: float
    bin_size: float


class MathematicalVolumeProfile:
    """
    Capital Wise
    Mathematical Volume Profile Engine

    يحسب:
    - POC
    - VAH
    - VAL
    - HVN
    - LVN
    - Volume Distribution
    """

    def __init__(
        self,
        bins: int = 120,
        value_area: float = 0.70,
    ):
        if bins < 10:
            raise ValueError("bins must be >= 10")

        if not 0 < value_area <= 1:
            raise ValueError("value_area must be between 0 and 1")

        self.bins = bins
        self.value_area = value_area

    def calculate(
        self,
        df: pd.DataFrame,
    ) -> VolumeProfileResult:

        required = {
            "high",
            "low",
            "close",
            "volume",
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing columns: {sorted(missing)}"
            )

        data = df[
            ["high", "low", "close", "volume"]
        ].dropna().copy()

        if data.empty:
            raise ValueError("No valid market data")

        prices = data["close"].to_numpy(dtype=float)
        volumes = data["volume"].to_numpy(dtype=float)

        price_low = float(data["low"].min())
        price_high = float(data["high"].max())

        if price_high <= price_low:
            raise ValueError("Invalid price range")

        edges = np.linspace(
            price_low,
            price_high,
            self.bins + 1,
        )

        bin_size = float(edges[1] - edges[0])

        indices = np.digitize(
            prices,
            edges,
            right=False,
        ) - 1

        indices = np.clip(
            indices,
            0,
            self.bins - 1,
        )

        volume_distribution = np.zeros(
            self.bins,
            dtype=float,
        )

        np.add.at(
            volume_distribution,
            indices,
            volumes,
        )

        centers = (
            edges[:-1] + edges[1:]
        ) / 2.0

        total_volume = float(
            volume_distribution.sum()
        )

        if total_volume <= 0:
            raise ValueError("Total volume must be > 0")

        # --------------------------------------------------
        # POC
        # --------------------------------------------------

        poc_index = int(
            np.argmax(volume_distribution)
        )

        poc = float(centers[poc_index])

        # --------------------------------------------------
        # Value Area
        # --------------------------------------------------

        target_volume = (
            total_volume * self.value_area
        )

        included = {poc_index}

        accumulated = float(
            volume_distribution[poc_index]
        )

        while accumulated < target_volume:

            left = min(included) - 1
            right = max(included) + 1

            left_volume = (
                volume_distribution[left]
                if left >= 0
                else -1
            )

            right_volume = (
                volume_distribution[right]
                if right < self.bins
                else -1
            )

            if left_volume < 0 and right_volume < 0:
                break

            if right_volume >= left_volume:
                selected = right
            else:
                selected = left

            included.add(selected)

            accumulated += float(
                volume_distribution[selected]
            )

        va_indices = sorted(included)

        val = float(
            centers[min(va_indices)]
        )

        vah = float(
            centers[max(va_indices)]
        )

        # --------------------------------------------------
        # HVN / LVN
        # --------------------------------------------------

        mean_volume = float(
            np.mean(volume_distribution)
        )

        std_volume = float(
            np.std(volume_distribution)
        )

        hvn_threshold = (
            mean_volume + 0.75 * std_volume
        )

        lvn_threshold = max(
            mean_volume - 0.75 * std_volume,
            0.0,
        )

        hvn = centers[
            volume_distribution >= hvn_threshold
        ]

        lvn = centers[
            volume_distribution <= lvn_threshold
        ]

        return VolumeProfileResult(
            poc=poc,
            vah=vah,
            val=val,
            hvn=hvn.tolist(),
            lvn=lvn.tolist(),
            total_volume=total_volume,
            value_area_volume=accumulated,
            value_area_percentage=(
                accumulated / total_volume
            ),
            bin_size=bin_size,
        )
