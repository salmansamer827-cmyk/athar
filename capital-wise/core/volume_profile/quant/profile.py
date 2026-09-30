from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .allocation import allocate_candle_volume
from .distribution import (
    normalize_volume,
    normalized_entropy,
)
from .statistics import (
    weighted_mean,
    weighted_variance,
    weighted_std,
    weighted_skewness,
    weighted_kurtosis,
)
from .nodes import detect_volume_nodes
from .binning import AdaptiveBinning


@dataclass(frozen=True)
class QuantProfile:
    price_low: float
    price_high: float

    bins: int
    bin_size: float

    total_volume: float

    poc: float
    vah: float
    val: float

    weighted_mean: float
    variance: float
    std: float
    skewness: float
    kurtosis: float

    entropy: float
    volume_concentration: float

    prices: np.ndarray
    volume_distribution: np.ndarray
    probability_distribution: np.ndarray

    hvn_nodes: list
    lvn_nodes: list


class QuantProfileEngine:

    def __init__(
        self,
        value_area: float = 0.70,
        min_bins: int = 40,
        max_bins: int = 300,
    ):

        if not 0.50 <= value_area <= 0.99:
            raise ValueError(
                "value_area must be between 0.50 and 0.99"
            )

        self.value_area = value_area

        self.binning = AdaptiveBinning(
            min_bins=min_bins,
            max_bins=max_bins,
        )

    def calculate(
        self,
        df: pd.DataFrame,
        tick_size: float | None = None,
    ) -> QuantProfile:

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
        ].copy()

        if data.empty:
            raise ValueError(
                "DataFrame cannot be empty"
            )

        if data.isna().any().any():
            raise ValueError(
                "OHLCV contains NaN values"
            )

        if (data["volume"] < 0).any():
            raise ValueError(
                "Volume cannot be negative"
            )

        if (data["high"] < data["low"]).any():
            raise ValueError(
                "High cannot be lower than Low"
            )

        price_low = float(
            data["low"].min()
        )

        price_high = float(
            data["high"].max()
        )

        if price_high <= price_low:
            raise ValueError(
                "Price range must be > 0"
            )

        total_volume = float(
            data["volume"].sum()
        )

        if total_volume <= 0:
            raise ValueError(
                "Total volume must be > 0"
            )

        config = self.binning.calculate(
            price_low=price_low,
            price_high=price_high,
            observations=len(data),
            tick_size=tick_size,
        )

        edges = np.linspace(
            config.price_low,
            config.price_high,
            config.bins + 1,
        )

        profile_volume = np.zeros(
            config.bins,
            dtype=np.float64,
        )

        for row in data.itertuples(
            index=False
        ):

            candle_distribution = (
                allocate_candle_volume(
                    low=float(row.low),
                    high=float(row.high),
                    volume=float(row.volume),
                    bin_edges=edges,
                )
            )

            profile_volume += (
                candle_distribution
            )

        allocated_volume = float(
            profile_volume.sum()
        )

        conservation_error = abs(
            allocated_volume
            - total_volume
        )

        tolerance = max(
            1e-9,
            total_volume * 1e-10,
        )

        if conservation_error > tolerance:
            raise RuntimeError(
                "Volume conservation failed: "
                f"error={conservation_error}"
            )

        prices = (
            edges[:-1] + edges[1:]
        ) / 2.0

        probability = normalize_volume(
            profile_volume
        )

        poc_index = int(
            np.argmax(profile_volume)
        )

        poc = float(
            prices[poc_index]
        )

        vah, val = self._value_area(
            prices,
            profile_volume,
            poc_index,
        )

        mean = weighted_mean(
            prices,
            profile_volume,
        )

        variance = weighted_variance(
            prices,
            profile_volume,
        )

        std = weighted_std(
            prices,
            profile_volume,
        )

        skewness = weighted_skewness(
            prices,
            profile_volume,
        )

        kurtosis = weighted_kurtosis(
            prices,
            profile_volume,
        )

        entropy = normalized_entropy(
            profile_volume
        )

        concentration = float(
            np.sum(
                probability ** 2
            )
        )

        hvn, lvn = detect_volume_nodes(
            prices,
            profile_volume,
        )

        return QuantProfile(
            price_low=price_low,
            price_high=price_high,
            bins=config.bins,
            bin_size=config.bin_size,
            total_volume=total_volume,
            poc=poc,
            vah=vah,
            val=val,
            weighted_mean=mean,
            variance=variance,
            std=std,
            skewness=skewness,
            kurtosis=kurtosis,
            entropy=entropy,
            volume_concentration=concentration,
            prices=prices,
            volume_distribution=profile_volume,
            probability_distribution=probability,
            hvn_nodes=hvn,
            lvn_nodes=lvn,
        )

    def _value_area(
        self,
        prices: np.ndarray,
        volume: np.ndarray,
        poc_index: int,
    ) -> tuple[float, float]:

        target = (
            volume.sum()
            * self.value_area
        )

        included_volume = float(
            volume[poc_index]
        )

        left = poc_index
        right = poc_index

        while included_volume < target:

            left_volume = (
                volume[left - 1]
                if left > 0
                else -1
            )

            right_volume = (
                volume[right + 1]
                if right < len(volume) - 1
                else -1
            )

            if left_volume < 0 and right_volume < 0:
                break

            if right_volume > left_volume:

                right += 1
                included_volume += (
                    volume[right]
                )

            else:

                left -= 1
                included_volume += (
                    volume[left]
                )

        return (
            float(prices[right]),
            float(prices[left]),
        )
