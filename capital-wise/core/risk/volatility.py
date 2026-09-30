from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class VolatilityResult:
    current_atr: float
    baseline_atr: float
    volatility_ratio: float


class VolatilityEngine:
    """
    CAPITAL WISE

    Market volatility engine.

    Calculates:

        True Range
            ↓
        Current ATR
            ↓
        Historical Baseline ATR
            ↓
        Volatility Ratio
    """

    def __init__(
        self,
        atr_period: int = 14,
        baseline_period: int = 50,
    ) -> None:

        if atr_period <= 0:
            raise ValueError(
                "atr_period must be > 0"
            )

        if baseline_period < atr_period:
            raise ValueError(
                "baseline_period must be >= atr_period"
            )

        self.atr_period = atr_period
        self.baseline_period = baseline_period

    def calculate(
        self,
        df: pd.DataFrame,
    ) -> VolatilityResult:

        required_columns = {
            "high",
            "low",
            "close",
        }

        missing = (
            required_columns
            - set(df.columns)
        )

        if missing:
            raise ValueError(
                "Missing columns: "
                f"{sorted(missing)}"
            )

        if len(df) < self.baseline_period:
            raise ValueError(
                "Insufficient candles for "
                "volatility calculation"
            )

        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        previous_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = (
            true_range
            .rolling(
                window=self.atr_period,
                min_periods=self.atr_period,
            )
            .mean()
        )

        atr = atr.dropna()

        if len(atr) < self.baseline_period:
            raise ValueError(
                "Insufficient ATR observations "
                "for baseline calculation"
            )

        current_atr = float(
            atr.iloc[-1]
        )

        baseline_atr = float(
            atr.iloc[
                -self.baseline_period:
            ].mean()
        )

        if baseline_atr <= 0:
            raise ValueError(
                "Baseline ATR must be > 0"
            )

        volatility_ratio = (
            current_atr
            / baseline_atr
        )

        return VolatilityResult(
            current_atr=current_atr,
            baseline_atr=baseline_atr,
            volatility_ratio=volatility_ratio,
        )
