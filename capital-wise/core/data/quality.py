from __future__ import annotations

from dataclasses import dataclass

import math

from core.data.models import OHLCV


@dataclass(frozen=True)
class DataQualityReport:
    rows: int

    valid: bool

    missing_values: int
    duplicate_timestamps: int

    invalid_prices: int
    invalid_ohlc: int

    negative_volume: int

    invalid_timestamps: int

    total_volume: float

    errors: tuple[str, ...]


class DataQualityEngine:
    """
    CAPITAL WISE

    High-integrity market data validation.

    Every candle must satisfy:

        timestamp > 0

        open  > 0
        high  > 0
        low   > 0
        close > 0

        high >= max(open, close)
        low  <= min(open, close)

        volume >= 0
    """

    def validate(
        self,
        candles: list[OHLCV],
    ) -> DataQualityReport:

        errors = []

        missing_values = 0
        duplicate_timestamps = 0

        invalid_prices = 0
        invalid_ohlc = 0
        negative_volume = 0
        invalid_timestamps = 0

        timestamps = set()

        for index, candle in enumerate(
            candles
        ):

            values = [
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
            ]

            # -------------------------
            # Missing / NaN / Infinity
            # -------------------------

            for value in values:

                if value is None:

                    missing_values += 1

                    errors.append(
                        f"row {index}: "
                        "missing value"
                    )

                    break

                if isinstance(
                    value,
                    float,
                ) and not math.isfinite(value):

                    missing_values += 1

                    errors.append(
                        f"row {index}: "
                        "non-finite value"
                    )

                    break

            # -------------------------
            # Timestamp
            # -------------------------

            if candle.timestamp <= 0:

                invalid_timestamps += 1

                errors.append(
                    f"row {index}: "
                    "invalid timestamp"
                )

            if candle.timestamp in timestamps:

                duplicate_timestamps += 1

                errors.append(
                    f"row {index}: "
                    "duplicate timestamp"
                )

            timestamps.add(
                candle.timestamp
            )

            # -------------------------
            # Prices
            # -------------------------

            prices = [
                candle.open,
                candle.high,
                candle.low,
                candle.close,
            ]

            if any(
                price <= 0
                for price in prices
            ):

                invalid_prices += 1

                errors.append(
                    f"row {index}: "
                    "invalid price"
                )

            # -------------------------
            # OHLC Structure
            # -------------------------

            if (
                candle.high
                < max(
                    candle.open,
                    candle.close,
                )
                or
                candle.low
                > min(
                    candle.open,
                    candle.close,
                )
                or
                candle.high < candle.low
            ):

                invalid_ohlc += 1

                errors.append(
                    f"row {index}: "
                    "invalid OHLC structure"
                )

            # -------------------------
            # Volume
            # -------------------------

            if candle.volume < 0:

                negative_volume += 1

                errors.append(
                    f"row {index}: "
                    "negative volume"
                )

        total_volume = sum(
            candle.volume
            for candle in candles
            if (
                candle.volume is not None
                and math.isfinite(
                    candle.volume
                )
                and candle.volume >= 0
            )
        )

        valid = (
            len(errors) == 0
        )

        return DataQualityReport(
            rows=len(candles),

            valid=valid,

            missing_values=(
                missing_values
            ),

            duplicate_timestamps=(
                duplicate_timestamps
            ),

            invalid_prices=(
                invalid_prices
            ),

            invalid_ohlc=(
                invalid_ohlc
            ),

            negative_volume=(
                negative_volume
            ),

            invalid_timestamps=(
                invalid_timestamps
            ),

            total_volume=(
                total_volume
            ),

            errors=tuple(errors),
        )
