from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinConfiguration:
    bins: int
    price_low: float
    price_high: float
    bin_size: float


class AdaptiveBinning:
    """
    Capital Wise
    Adaptive Price Binning Engine.

    الهدف:
    اختيار resolution مناسب للـVolume Profile
    بدل استخدام عدد bins ثابت دائمًا.
    """

    def __init__(
        self,
        min_bins: int = 40,
        max_bins: int = 300,
    ):
        if min_bins < 10:
            raise ValueError(
                "min_bins must be >= 10"
            )

        if max_bins <= min_bins:
            raise ValueError(
                "max_bins must be > min_bins"
            )

        self.min_bins = min_bins
        self.max_bins = max_bins

    def calculate(
        self,
        price_low: float,
        price_high: float,
        observations: int,
        tick_size: float | None = None,
    ) -> BinConfiguration:

        if price_low <= 0:
            raise ValueError(
                "price_low must be > 0"
            )

        if price_high <= price_low:
            raise ValueError(
                "price_high must be > price_low"
            )

        if observations < 2:
            raise ValueError(
                "observations must be >= 2"
            )

        price_range = (
            price_high - price_low
        )

        # قاعدة أولية تعتمد على حجم العينة.
        # sqrt(N) resolution أكثر تحفظًا
        # من اختيار bins عشوائي.
        estimated_bins = int(
            observations ** 0.5
        )

        bins = max(
            self.min_bins,
            estimated_bins,
        )

        bins = min(
            self.max_bins,
            bins,
        )

        # احترام Tick Size عندما يكون معروفًا.
        if tick_size is not None:

            if tick_size <= 0:
                raise ValueError(
                    "tick_size must be > 0"
                )

            maximum_bins_by_tick = int(
                price_range / tick_size
            )

            if maximum_bins_by_tick >= self.min_bins:
                bins = min(
                    bins,
                    maximum_bins_by_tick,
                )

        bin_size = (
            price_range / bins
        )

        return BinConfiguration(
            bins=bins,
            price_low=price_low,
            price_high=price_high,
            bin_size=bin_size,
        )
