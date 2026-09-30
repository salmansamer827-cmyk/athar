"""
====================================================================
                    EXCORA QUANT MTF MASTER
====================================================================
MULTI-TIMEFRAME QUANT SIGNAL / RESEARCH ENGINE

TIMEFRAME ARCHITECTURE
----------------------
1D  -> Macro Trend
4H  -> Trend Confirmation + Market Structure
1H  -> Liquidity Sweep + MSS/CHoCH + Displacement
15M -> Execution Context + Quant Filters

CORE COMPONENTS
---------------
EMA 50/200
ATR
Relative Volume
VWAP
Volume Profile
FVG
Order Block
BOS / CHoCH
Liquidity Sweep
Candle Quality
Momentum
Market Regime
Real Score 0-100
Risk Engine
Backtesting Statistics
Monte Carlo
Walk-Forward Split

IMPORTANT
---------
SIGNAL / SCANNER ONLY
NO REAL ORDER EXECUTION

Only closed candles are used for live analysis.
This engine does NOT guarantee profitability.
Past performance does not guarantee future results.

TELEGRAM
--------
Telegram has been completely separated into:
    telegram_notifier.py

The quantitative engine contains no Telegram message formatting.
====================================================================
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import ccxt
import numpy as np
import pandas as pd

from telegram_notifier import TelegramNotifier


# ====================================================================
# LOGGING
# ====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("EXCORA")


# ====================================================================
# CONFIGURATION
# ====================================================================

@dataclass
class ExcoraConfig:
    balance: float = 100.0
    risk_percent: float = 1.0
    reward_risk: float = 3.0
    minimum_score: float = 75.0

    ema_fast: int = 50
    ema_slow: int = 200
    atr_period: int = 14
    volume_period: int = 20
    slope_period: int = 5

    structure_left: int = 3
    structure_right: int = 3
    liquidity_lookback: int = 20

    vp_lookback: int = 96
    vp_bins: int = 24

    fvg_lookback: int = 12
    order_block_lookback: int = 20

    atr_stop_buffer: float = 0.25
    minimum_stop_atr: float = 0.50
    maximum_stop_atr: float = 4.00
    maximum_atr_percent: float = 8.0
    minimum_relative_volume: float = 0.80

    scan_interval: int = 120
    candles: int = 350

    exchange_id: str = "binance"


# ====================================================================
# MAIN ENGINE
# ====================================================================

class ExcoraQuantMTFMaster:
    """EXCORA quantitative multi-timeframe signal engine."""

    REQUIRED_TIMEFRAMES = ("1d", "4h", "1h", "15m")

    def __init__(
        self,
        symbol: str,
        config: ExcoraConfig | None = None,
    ) -> None:
        self.symbol = symbol
        self.config = config or ExcoraConfig()

        exchange_class = getattr(ccxt, self.config.exchange_id)

        self.exchange = exchange_class(
            {
                "enableRateLimit": True,
                "options": {
                    "defaultType": "future",
                },
            }
        )

        self.data: dict[str, pd.DataFrame] = {}

    # =================================================================
    # UTILITIES
    # =================================================================

    @staticmethod
    def valid(value: Any) -> bool:
        try:
            return bool(np.isfinite(float(value)))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def closed(df: pd.DataFrame) -> pd.Series:
        if len(df) < 3:
            raise ValueError("Insufficient candles.")
        # Last exchange candle may still be forming.
        return df.iloc[-2]

    @staticmethod
    def timeframe_minutes(timeframe: str) -> int:
        mapping = {
            "15m": 15,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }
        if timeframe not in mapping:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return mapping[timeframe]

    # =================================================================
    # DATA FETCH
    # =================================================================

    def fetch(
        self,
        timeframe: str,
        limit: int | None = None,
        retries: int = 3,
    ) -> pd.DataFrame | None:
        limit = limit or self.config.candles

        for attempt in range(1, retries + 1):
            try:
                raw = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=timeframe,
                    limit=limit,
                )

                if not raw:
                    raise ValueError("Empty OHLCV.")

                df = pd.DataFrame(
                    raw,
                    columns=[
                        "Timestamp",
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume",
                    ],
                )

                df["Timestamp"] = pd.to_datetime(
                    df["Timestamp"],
                    unit="ms",
                    utc=True,
                )

                numeric = [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                ]

                for col in numeric:
                    df[col] = pd.to_numeric(
                        df[col],
                        errors="coerce",
                    )

                df.dropna(subset=numeric, inplace=True)
                df.drop_duplicates(
                    subset=["Timestamp"],
                    inplace=True,
                )
                df.sort_values("Timestamp", inplace=True)
                df.reset_index(drop=True, inplace=True)

                invalid = (
                    (df["High"] < df["Low"])
                    | (df["High"] < df["Open"])
                    | (df["High"] < df["Close"])
                    | (df["Low"] > df["Open"])
                    | (df["Low"] > df["Close"])
                    | (df["Volume"] < 0)
                )

                df = df.loc[~invalid].copy()
                df.reset_index(drop=True, inplace=True)

                minimum = self.config.ema_slow + 50
                if len(df) < minimum:
                    raise ValueError(
                        f"Insufficient history: {len(df)} < {minimum}"
                    )

                self.data[timeframe] = df

                logger.info(
                    "DATA OK | %s | %s | %s candles",
                    self.symbol,
                    timeframe,
                    len(df),
                )

                return df

            except Exception as exc:
                logger.warning(
                    "DATA RETRY %s/%s | %s | %s | %s",
                    attempt,
                    retries,
                    self.symbol,
                    timeframe,
                    exc,
                )

                if attempt < retries:
                    time.sleep(2 ** (attempt - 1))

        return None

    # =================================================================
    # INDICATORS
    # =================================================================

    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["EMA50"] = df["Close"].ewm(
            span=self.config.ema_fast,
            adjust=False,
        ).mean()

        df["EMA200"] = df["Close"].ewm(
            span=self.config.ema_slow,
            adjust=False,
        ).mean()

        p = self.config.slope_period

        df["EMA50_Slope"] = (
            df["EMA50"] - df["EMA50"].shift(p)
        )

        df["EMA200_Slope"] = (
            df["EMA200"] - df["EMA200"].shift(p)
        )

        previous_close = df["Close"].shift(1)

        tr1 = df["High"] - df["Low"]
        tr2 = (df["High"] - previous_close).abs()
        tr3 = (df["Low"] - previous_close).abs()

        df["TR"] = pd.concat(
            [tr1, tr2, tr3],
            axis=1,
        ).max(axis=1)

        # Wilder-style ATR.
        df["ATR"] = df["TR"].ewm(
            alpha=1 / self.config.atr_period,
            adjust=False,
        ).mean()

        df["ATR_Pct"] = (
            df["ATR"] / df["Close"]
        ) * 100.0

        df["EMA_Separation_ATR"] = (
            (df["EMA50"] - df["EMA200"]).abs()
            / df["ATR"].replace(0, np.nan)
        )

        df["EMA50_Slope_ATR"] = (
            df["EMA50_Slope"]
            / df["ATR"].replace(0, np.nan)
        )

        df["EMA200_Slope_ATR"] = (
            df["EMA200_Slope"]
            / df["ATR"].replace(0, np.nan)
        )

        df["Volume_MA"] = df["Volume"].rolling(
            self.config.volume_period
        ).mean()

        df["Relative_Volume"] = (
            df["Volume"]
            / df["Volume_MA"].replace(0, np.nan)
        )

        df["Range"] = df["High"] - df["Low"]
        df["Body"] = (
            df["Close"] - df["Open"]
        ).abs()

        df["Body_Ratio"] = (
            df["Body"]
            / df["Range"].replace(0, np.nan)
        )

        df["Upper_Wick"] = (
            df["High"]
            - df[["Open", "Close"]].max(axis=1)
        )

        df["Lower_Wick"] = (
            df[["Open", "Close"]].min(axis=1)
            - df["Low"]
        )

        df["ROC5"] = (
            df["Close"].pct_change(5) * 100.0
        )

        # UTC daily session VWAP.
        typical_price = (
            df["High"] + df["Low"] + df["Close"]
        ) / 3.0

        session = df["Timestamp"].dt.floor("D")
        pv = typical_price * df["Volume"]

        cumulative_pv = pv.groupby(session).cumsum()
        cumulative_volume = (
            df["Volume"].groupby(session).cumsum()
        )

        df["VWAP"] = (
            cumulative_pv
            / cumulative_volume.replace(0, np.nan)
        )

        left = self.config.structure_left
        right = self.config.structure_right
        window = left + right + 1

        df["SwingHigh"] = (
            df["High"]
            == df["High"].rolling(
                window,
                center=True,
            ).max()
        )

        df["SwingLow"] = (
            df["Low"]
            == df["Low"].rolling(
                window,
                center=True,
            ).min()
        )

        # Three-candle fair value gaps.
        df["BullishFVG"] = (
            df["Low"] > df["High"].shift(2)
        )

        df["BearishFVG"] = (
            df["High"] < df["Low"].shift(2)
        )

        df["BullishFVG_Low"] = np.where(
            df["BullishFVG"],
            df["High"].shift(2),
            np.nan,
        )

        df["BullishFVG_High"] = np.where(
            df["BullishFVG"],
            df["Low"],
            np.nan,
        )

        df["BearishFVG_Low"] = np.where(
            df["BearishFVG"],
            df["High"],
            np.nan,
        )

        df["BearishFVG_High"] = np.where(
            df["BearishFVG"],
            df["Low"].shift(2),
            np.nan,
        )

        df.replace(
            [np.inf, -np.inf],
            np.nan,
            inplace=True,
        )

        return df

    # =================================================================
    # MARKET STRUCTURE
    # =================================================================

    @staticmethod
    def structure_state(df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < 20:
            return {
                "structure": "UNKNOWN",
                "bos": None,
                "choch": None,
                "swing_high": np.nan,
                "swing_low": np.nan,
            }

        # Exclude current/forming candle.
        closed = df.iloc[:-1].copy()

        swing_highs = closed.loc[closed["SwingHigh"]]
        swing_lows = closed.loc[closed["SwingLow"]]

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {
                "structure": "UNKNOWN",
                "bos": None,
                "choch": None,
                "swing_high": np.nan,
                "swing_low": np.nan,
            }

        last_high = float(swing_highs.iloc[-1]["High"])
        previous_high = float(swing_highs.iloc[-2]["High"])
        last_low = float(swing_lows.iloc[-1]["Low"])
        previous_low = float(swing_lows.iloc[-2]["Low"])

        if last_high > previous_high and last_low > previous_low:
            structure = "BULLISH"
        elif last_high < previous_high and last_low < previous_low:
            structure = "BEARISH"
        else:
            structure = "RANGE"

        candle = closed.iloc[-1]

        bos = None
        if candle["Close"] > last_high:
            bos = "BULLISH_BOS"
        elif candle["Close"] < last_low:
            bos = "BEARISH_BOS"

        choch = None
        if structure == "BEARISH" and candle["Close"] > last_high:
            choch = "BULLISH_CHOCH"
        elif structure == "BULLISH" and candle["Close"] < last_low:
            choch = "BEARISH_CHOCH"

        return {
            "structure": structure,
            "bos": bos,
            "choch": choch,
            "swing_high": last_high,
            "swing_low": last_low,
        }

    # =================================================================
    # LIQUIDITY SWEEP
    # =================================================================

    def liquidity_sweep(
        self,
        df: pd.DataFrame,
        direction: str,
    ) -> dict[str, Any]:
        lookback = self.config.liquidity_lookback

        if len(df) < lookback + 5:
            return {"detected": False, "type": None}

        current = df.iloc[-2]
        previous = df.iloc[-(lookback + 2):-2]

        previous_high = float(previous["High"].max())
        previous_low = float(previous["Low"].min())

        if direction == "BUY":
            swept = current["Low"] < previous_low
            recovered = current["Close"] > previous_low

            if swept and recovered:
                return {
                    "detected": True,
                    "type": "SELL_SIDE_LIQUIDITY",
                }

        elif direction == "SELL":
            swept = current["High"] > previous_high
            rejected = current["Close"] < previous_high

            if swept and rejected:
                return {
                    "detected": True,
                    "type": "BUY_SIDE_LIQUIDITY",
                }

        return {"detected": False, "type": None}

    # =================================================================
    # DISPLACEMENT
    # =================================================================

    def displacement(
        self,
        df: pd.DataFrame,
        direction: str,
    ) -> bool:
        candle = self.closed(df)
        atr = float(candle["ATR"])
        body = float(candle["Body"])

        if atr <= 0:
            return False

        if direction == "BUY":
            return bool(
                candle["Close"] > candle["Open"]
                and body >= atr * 0.80
                and candle["Body_Ratio"] >= 0.60
            )

        if direction == "SELL":
            return bool(
                candle["Close"] < candle["Open"]
                and body >= atr * 0.80
                and candle["Body_Ratio"] >= 0.60
            )

        return False

    # =================================================================
    # FVG
    # =================================================================

    def recent_fvg(
        self,
        df: pd.DataFrame,
        direction: str,
    ) -> bool:
        lookback = self.config.fvg_lookback
        data = df.iloc[-(lookback + 2):-1]

        if direction == "BUY":
            return bool(data["BullishFVG"].any())

        if direction == "SELL":
            return bool(data["BearishFVG"].any())

        return False

    # =================================================================
    # ORDER BLOCK
    # =================================================================

    def recent_order_block(
        self,
        df: pd.DataFrame,
        direction: str,
    ) -> bool:
        lookback = self.config.order_block_lookback

        if len(df) < lookback + 5:
            return False

        data = df.iloc[-(lookback + 2):-1]

        for i in range(1, len(data)):
            previous = data.iloc[i - 1]
            current = data.iloc[i]

            current_atr = float(current["ATR"])
            if current_atr <= 0:
                continue

            current_body = abs(
                float(current["Close"] - current["Open"])
            )

            if direction == "BUY":
                if (
                    previous["Close"] < previous["Open"]
                    and current["Close"] > current["Open"]
                    and current_body >= current_atr * 0.80
                ):
                    return True

            elif direction == "SELL":
                if (
                    previous["Close"] > previous["Open"]
                    and current["Close"] < current["Open"]
                    and current_body >= current_atr * 0.80
                ):
                    return True

        return False

    # =================================================================
    # VOLUME PROFILE
    # =================================================================

    def volume_profile(self, df: pd.DataFrame) -> dict[str, float]:
        lookback = self.config.vp_lookback
        bins = self.config.vp_bins

        if len(df) < lookback + 2:
            return {
                "POC": np.nan,
                "VAH": np.nan,
                "VAL": np.nan,
            }

        data = df.iloc[-(lookback + 2):-1].copy()

        price_low = float(data["Low"].min())
        price_high = float(data["High"].max())

        if price_high <= price_low:
            return {
                "POC": price_low,
                "VAH": price_high,
                "VAL": price_low,
            }

        edges = np.linspace(
            price_low,
            price_high,
            bins + 1,
        )

        centers = (
            edges[:-1] + edges[1:]
        ) / 2.0

        volume_by_bin = np.zeros(bins)

        typical = (
            data["High"]
            + data["Low"]
            + data["Close"]
        ) / 3.0

        for price, volume in zip(
            typical,
            data["Volume"],
        ):
            index = (
                np.searchsorted(
                    edges,
                    price,
                    side="right",
                )
                - 1
            )

            index = max(0, min(bins - 1, index))
            volume_by_bin[index] += float(volume)

        poc_index = int(np.argmax(volume_by_bin))
        total_volume = float(volume_by_bin.sum())

        if total_volume <= 0:
            return {
                "POC": np.nan,
                "VAH": np.nan,
                "VAL": np.nan,
            }

        target = total_volume * 0.70
        selected = {poc_index}
        cumulative = float(volume_by_bin[poc_index])

        left = poc_index - 1
        right = poc_index + 1

        while cumulative < target:
            left_volume = (
                volume_by_bin[left]
                if left >= 0
                else -1
            )

            right_volume = (
                volume_by_bin[right]
                if right < bins
                else -1
            )

            if left_volume < 0 and right_volume < 0:
                break

            if right_volume >= left_volume:
                if right < bins:
                    selected.add(right)
                    cumulative += float(right_volume)
                    right += 1
            else:
                if left >= 0:
                    selected.add(left)
                    cumulative += float(left_volume)
                    left -= 1

        value_indices = sorted(selected)

        val = float(edges[value_indices[0]])
        vah = float(edges[value_indices[-1] + 1])
        poc = float(centers[poc_index])

        return {
            "POC": poc,
            "VAH": vah,
            "VAL": val,
        }

    # =================================================================
    # VWAP / VP LOCATION
    # =================================================================

    def location_score(
        self,
        df: pd.DataFrame,
        direction: str,
    ) -> dict[str, Any]:
        candle = self.closed(df)
        price = float(candle["Close"])
        vwap = float(candle["VWAP"])

        vp = self.volume_profile(df)
        poc = vp["POC"]
        vah = vp["VAH"]
        val = vp["VAL"]

        if not all(
            self.valid(x)
            for x in [price, vwap, poc, vah, val]
        ):
            return {
                "vwap": False,
                "value_area": False,
                "poc": False,
                "vp": vp,
            }

        if direction == "BUY":
            vwap_ok = price > vwap
            value_ok = price <= vah
        else:
            vwap_ok = price < vwap
            value_ok = price >= val

        poc_ok = (
            abs(price - poc)
            <= abs(vah - val) * 0.15
        )

        return {
            "vwap": vwap_ok,
            "value_area": value_ok,
            "poc": poc_ok,
            "vp": vp,
        }

    # =================================================================
    # MARKET REGIME
    # =================================================================

    def market_regime(self, df: pd.DataFrame) -> str:
        candle = self.closed(df)

        atr_pct = float(candle["ATR_Pct"])
        separation = float(candle["EMA_Separation_ATR"])
        relative_volume = float(candle["Relative_Volume"])

        if not all(
            self.valid(v)
            for v in [atr_pct, separation, relative_volume]
        ):
            return "INVALID"

        if atr_pct > self.config.maximum_atr_percent:
            return "EXTREME_VOLATILITY"

        if separation < 0.20:
            return "RANGE"

        if (
            separation >= 1.00
            and relative_volume >= 0.80
        ):
            return "TRENDING"

        return "NORMAL"

    # =================================================================
    # TREND
    # =================================================================

    def trend(self, df: pd.DataFrame) -> dict[str, Any]:
        candle = self.closed(df)

        ema50 = float(candle["EMA50"])
        ema200 = float(candle["EMA200"])
        slope50 = float(candle["EMA50_Slope"])
        close = float(candle["Close"])
        separation = float(candle["EMA_Separation_ATR"])

        if not all(
            self.valid(v)
            for v in [
                ema50,
                ema200,
                slope50,
                close,
                separation,
            ]
        ):
            return {
                "trend": "INVALID",
                "strength": 0.0,
            }

        if ema50 > ema200 and slope50 > 0:
            state = "BULLISH"
        elif ema50 < ema200 and slope50 < 0:
            state = "BEARISH"
        else:
            state = "NEUTRAL"

        strength = min(100.0, separation * 50.0)

        return {
            "trend": state,
            "strength": round(strength, 2),
            "ema50": ema50,
            "ema200": ema200,
            "slope_atr": float(candle["EMA50_Slope_ATR"]),
            "separation_atr": separation,
        }

    # =================================================================
    # REAL SCORE ENGINE
    # =================================================================

    def score(
        self,
        direction: str,
        trend_1d: dict[str, Any],
        trend_4h: dict[str, Any],
        structure_1d: dict[str, Any],
        structure_4h: dict[str, Any],
        structure_1h: dict[str, Any],
        liquidity_1h: dict[str, Any],
        displacement_1h: bool,
        df_15m: pd.DataFrame,
        regime: str,
        location: dict[str, Any],
    ) -> tuple[float, dict[str, float]]:
        candle = self.closed(df_15m)
        points: dict[str, float] = {}

        points["1D_TREND"] = (
            15.0
            if (
                (
                    direction == "BUY"
                    and trend_1d["trend"] == "BULLISH"
                )
                or (
                    direction == "SELL"
                    and trend_1d["trend"] == "BEARISH"
                )
            )
            else 0.0
        )

        points["4H_TREND"] = (
            15.0
            if (
                (
                    direction == "BUY"
                    and trend_4h["trend"] == "BULLISH"
                )
                or (
                    direction == "SELL"
                    and trend_4h["trend"] == "BEARISH"
                )
            )
            else 0.0
        )

        desired_structure = (
            "BULLISH"
            if direction == "BUY"
            else "BEARISH"
        )

        structure_points = 0.0

        if structure_1d["structure"] == desired_structure:
            structure_points += 5.0

        if structure_4h["structure"] == desired_structure:
            structure_points += 5.0

        if structure_1h["structure"] == desired_structure:
            structure_points += 5.0

        points["STRUCTURE"] = structure_points

        points["LIQUIDITY"] = (
            10.0
            if liquidity_1h["detected"]
            else 0.0
        )

        points["DISPLACEMENT"] = (
            5.0
            if displacement_1h
            else 0.0
        )

        ema50 = float(candle["EMA50"])
        ema200 = float(candle["EMA200"])

        ema_ok = (
            (
                direction == "BUY"
                and ema50 > ema200
            )
            or (
                direction == "SELL"
                and ema50 < ema200
            )
        )

        points["EMA_ALIGNMENT"] = 8.0 if ema_ok else 0.0

        separation = float(candle["EMA_Separation_ATR"])

        if separation >= 1.0:
            points["EMA_SEPARATION"] = 5.0
        elif separation >= 0.50:
            points["EMA_SEPARATION"] = 3.0
        else:
            points["EMA_SEPARATION"] = 0.0

        slope = float(candle["EMA50_Slope_ATR"])

        slope_ok = (
            (
                direction == "BUY"
                and slope > 0.05
            )
            or (
                direction == "SELL"
                and slope < -0.05
            )
        )

        points["EMA_SLOPE"] = 5.0 if slope_ok else 0.0

        relative_volume = float(candle["Relative_Volume"])

        if relative_volume >= 1.20:
            points["VOLUME"] = 5.0
        elif relative_volume >= 1.00:
            points["VOLUME"] = 3.0
        elif relative_volume >= self.config.minimum_relative_volume:
            points["VOLUME"] = 1.0
        else:
            points["VOLUME"] = 0.0

        points["VWAP"] = 4.0 if location["vwap"] else 0.0

        points["VOLUME_PROFILE"] = (
            4.0
            if (
                location["value_area"]
                or location["poc"]
            )
            else 0.0
        )

        points["FVG"] = (
            3.0
            if self.recent_fvg(df_15m, direction)
            else 0.0
        )

        points["ORDER_BLOCK"] = (
            3.0
            if self.recent_order_block(df_15m, direction)
            else 0.0
        )

        body_ratio = float(candle["Body_Ratio"])

        candle_direction = (
            candle["Close"] > candle["Open"]
            if direction == "BUY"
            else candle["Close"] < candle["Open"]
        )

        points["CANDLE"] = (
            3.0
            if candle_direction and body_ratio >= 0.55
            else 1.0
            if candle_direction and body_ratio >= 0.35
            else 0.0
        )

        roc = float(candle["ROC5"])

        momentum_ok = (
            (
                direction == "BUY"
                and roc > 0
            )
            or (
                direction == "SELL"
                and roc < 0
            )
        )

        points["MOMENTUM"] = 5.0 if momentum_ok else 0.0

        if regime == "TRENDING":
            points["REGIME"] = 5.0
        elif regime == "NORMAL":
            points["REGIME"] = 2.0
        else:
            points["REGIME"] = 0.0

        total = sum(points.values())

        # Theoretical maximum remains 110.
        score = round(
            min(100.0, (total / 110.0) * 100.0),
            2,
        )

        return score, points

    # =================================================================
    # STOP LOSS
    # =================================================================

    def stop_loss(
        self,
        df: pd.DataFrame,
        direction: str,
    ) -> float:
        candle = self.closed(df)

        entry = float(candle["Close"])
        atr = float(candle["ATR"])

        if atr <= 0:
            raise ValueError("Invalid ATR.")

        lookback = 12
        structure = df.iloc[-(lookback + 2):-2]

        recent_low = float(structure["Low"].min())
        recent_high = float(structure["High"].max())

        buffer = atr * self.config.atr_stop_buffer

        if direction == "BUY":
            sl = recent_low - buffer
            if sl >= entry:
                sl = entry - atr
        else:
            sl = recent_high + buffer
            if sl <= entry:
                sl = entry + atr

        distance = abs(entry - sl)

        minimum = atr * self.config.minimum_stop_atr
        maximum = atr * self.config.maximum_stop_atr

        if distance < minimum:
            sl = (
                entry - minimum
                if direction == "BUY"
                else entry + minimum
            )

        distance = abs(entry - sl)

        if distance > maximum:
            raise ValueError("Structural stop is too wide.")

        return float(sl)

    # =================================================================
    # RISK ENGINE
    # =================================================================

    def risk_plan(
        self,
        entry: float,
        stop: float,
        direction: str,
    ) -> dict[str, float]:
        risk_amount = (
            self.config.balance
            * self.config.risk_percent
            / 100.0
        )

        if direction == "BUY":
            if stop >= entry:
                raise ValueError("BUY SL invalid.")

            distance = entry - stop
            tp = entry + distance * self.config.reward_risk

        elif direction == "SELL":
            if stop <= entry:
                raise ValueError("SELL SL invalid.")

            distance = stop - entry
            tp = entry - distance * self.config.reward_risk

        else:
            raise ValueError("Invalid direction.")

        if distance <= 0:
            raise ValueError("Invalid price risk.")

        quantity = risk_amount / distance
        notional = quantity * entry

        return {
            "entry": float(entry),
            "stop": float(stop),
            "tp": float(tp),
            "risk_usd": float(risk_amount),
            "risk_distance": float(distance),
            "risk_distance_pct": float(distance / entry * 100.0),
            "quantity": float(quantity),
            "notional": float(notional),
            "rr": float(self.config.reward_risk),
        }

    # =================================================================
    # COMPLETE ANALYSIS
    # =================================================================

    def analyze(self) -> dict[str, Any]:
        for tf in self.REQUIRED_TIMEFRAMES:
            if tf not in self.data:
                return {
                    "signal": "NEUTRAL",
                    "reason": f"Missing {tf} data.",
                }

        for tf in self.REQUIRED_TIMEFRAMES:
            self.data[tf] = self.indicators(self.data[tf])

        df_1d = self.data["1d"]
        df_4h = self.data["4h"]
        df_1h = self.data["1h"]
        df_15m = self.data["15m"]

        trend_1d = self.trend(df_1d)
        trend_4h = self.trend(df_4h)

        if (
            trend_1d["trend"] == "INVALID"
            or trend_4h["trend"] == "INVALID"
        ):
            return {
                "signal": "NEUTRAL",
                "reason": "Invalid HTF trend.",
            }

        if (
            trend_1d["trend"] == "BULLISH"
            and trend_4h["trend"] == "BULLISH"
        ):
            direction = "BUY"
        elif (
            trend_1d["trend"] == "BEARISH"
            and trend_4h["trend"] == "BEARISH"
        ):
            direction = "SELL"
        else:
            return {
                "signal": "NEUTRAL",
                "reason": "1D / 4H trend misalignment.",
                "trend_1d": trend_1d["trend"],
                "trend_4h": trend_4h["trend"],
            }

        structure_1d = self.structure_state(df_1d)
        structure_4h = self.structure_state(df_4h)
        structure_1h = self.structure_state(df_1h)

        liquidity_1h = self.liquidity_sweep(
            df_1h,
            direction,
        )

        displacement_1h = self.displacement(
            df_1h,
            direction,
        )

        regime = self.market_regime(df_15m)

        if regime in (
            "INVALID",
            "RANGE",
            "EXTREME_VOLATILITY",
        ):
            return {
                "signal": "NEUTRAL",
                "reason": f"Market regime rejected: {regime}",
                "trend_1d": trend_1d["trend"],
                "trend_4h": trend_4h["trend"],
                "regime": regime,
            }

        location = self.location_score(
            df_15m,
            direction,
        )

        score, components = self.score(
            direction,
            trend_1d,
            trend_4h,
            structure_1d,
            structure_4h,
            structure_1h,
            liquidity_1h,
            displacement_1h,
            df_15m,
            regime,
            location,
        )

        if score < self.config.minimum_score:
            return {
                "signal": "NEUTRAL",
                "reason": "Score below minimum.",
                "score": score,
                "score_components": components,
                "trend_1d": trend_1d["trend"],
                "trend_4h": trend_4h["trend"],
                "regime": regime,
                "liquidity": liquidity_1h,
            }

        candle = self.closed(df_15m)
        entry = float(candle["Close"])

        try:
            stop = self.stop_loss(
                df_15m,
                direction,
            )

            trade = self.risk_plan(
                entry,
                stop,
                direction,
            )

        except Exception as exc:
            return {
                "signal": "NEUTRAL",
                "reason": f"Risk rejected: {exc}",
                "score": score,
            }

        timestamp = candle["Timestamp"]

        signal_id = (
            f"{self.symbol}|"
            f"{direction}|"
            f"{timestamp.isoformat()}"
        )

        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        else:
            grade = "B"

        return {
            "signal": direction,
            "score": score,
            "grade": grade,
            "signal_id": signal_id,
            "timestamp": timestamp,

            "trend_1d": trend_1d,
            "trend_4h": trend_4h,

            "structure_1d": structure_1d,
            "structure_4h": structure_4h,
            "structure_1h": structure_1h,

            "liquidity": liquidity_1h,
            "displacement": displacement_1h,
            "regime": regime,
            "location": location,

            "fvg": self.recent_fvg(df_15m, direction),
            "order_block": self.recent_order_block(
                df_15m,
                direction,
            ),

            "relative_volume": float(
                candle["Relative_Volume"]
            ),
            "vwap": float(candle["VWAP"]),
            "atr": float(candle["ATR"]),
            "atr_pct": float(candle["ATR_Pct"]),
            "ema_separation_atr": float(
                candle["EMA_Separation_ATR"]
            ),
            "ema_slope_atr": float(
                candle["EMA50_Slope_ATR"]
            ),
            "roc5": float(candle["ROC5"]),

            "score_components": components,
            "trade": trade,
        }

    # =================================================================
    # LIVE SCAN
    # =================================================================

    def scan(self) -> dict[str, Any]:
        for tf in self.REQUIRED_TIMEFRAMES:
            if self.fetch(tf) is None:
                return {
                    "signal": "NEUTRAL",
                    "reason": f"Data unavailable: {tf}",
                }

        return self.analyze()


# ====================================================================
# PERFORMANCE STATISTICS
# ====================================================================

class ExcoraPerformance:
    @staticmethod
    def statistics(returns: list[float]) -> dict[str, Any]:
        if not returns:
            return {
                "trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy_R": 0.0,
                "max_drawdown_R": 0.0,
                "average_R": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "total_R": 0.0,
            }

        r = np.array(returns, dtype=float)

        wins = r[r > 0]
        losses = r[r < 0]

        win_rate = len(wins) / len(r) * 100.0

        gross_profit = float(wins.sum()) if len(wins) else 0.0
        gross_loss = float(abs(losses.sum())) if len(losses) else 0.0

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else np.inf
        )

        equity = np.cumsum(r)
        peaks = np.maximum.accumulate(equity)
        drawdown = equity - peaks

        max_drawdown = (
            abs(float(drawdown.min()))
            if len(drawdown)
            else 0.0
        )

        average = float(r.mean())

        std = (
            float(r.std(ddof=1))
            if len(r) > 1
            else 0.0
        )

        sharpe = (
            average / std * np.sqrt(len(r))
            if std > 0
            else 0.0
        )

        downside = r[r < 0]

        downside_std = (
            float(downside.std(ddof=1))
            if len(downside) > 1
            else 0.0
        )

        sortino = (
            average / downside_std * np.sqrt(len(r))
            if downside_std > 0
            else 0.0
        )

        return {
            "trades": int(len(r)),
            "wins": int(len(wins)),
            "losses": int(len(losses)),
            "win_rate": round(win_rate, 2),
            "profit_factor": (
                round(float(profit_factor), 3)
                if np.isfinite(profit_factor)
                else float("inf")
            ),
            "expectancy_R": round(average, 4),
            "average_R": round(average, 4),
            "total_R": round(float(r.sum()), 4),
            "max_drawdown_R": round(max_drawdown, 4),
            "sharpe": round(float(sharpe), 4),
            "sortino": round(float(sortino), 4),
        }


# ====================================================================
# MONTE CARLO
# ====================================================================

class ExcoraMonteCarlo:
    @staticmethod
    def simulate(
        returns: list[float],
        simulations: int = 5000,
    ) -> dict[str, Any]:
        if len(returns) < 5:
            return {
                "valid": False,
                "reason": "At least 5 trades required.",
            }

        r = np.array(returns, dtype=float)
        rng = np.random.default_rng(42)

        final_results = []
        max_drawdowns = []

        for _ in range(simulations):
            sample = rng.choice(
                r,
                size=len(r),
                replace=True,
            )

            equity = np.cumsum(sample)
            peaks = np.maximum.accumulate(equity)
            dd = equity - peaks

            final_results.append(float(equity[-1]))
            max_drawdowns.append(float(abs(dd.min())))

        final_array = np.array(final_results)
        dd_array = np.array(max_drawdowns)

        return {
            "valid": True,
            "simulations": simulations,
            "median_final_R": round(
                float(np.median(final_array)),
                4,
            ),
            "worst_final_R_5pct": round(
                float(np.percentile(final_array, 5)),
                4,
            ),
            "best_final_R_95pct": round(
                float(np.percentile(final_array, 95)),
                4,
            ),
            "median_max_drawdown_R": round(
                float(np.median(dd_array)),
                4,
            ),
            "worst_drawdown_R_95pct": round(
                float(np.percentile(dd_array, 95)),
                4,
            ),
        }


# ====================================================================
# SIMPLE BACKTEST ENGINE
# ====================================================================

class ExcoraBacktester:
    """
    Research backtester.

    IMPORTANT:
    A signal is evaluated only after a candle closes.

    If a future candle touches both SL and TP, it is classified as
    a loss/ambiguous case rather than assuming the favorable order.
    """

    def __init__(self, engine: ExcoraQuantMTFMaster) -> None:
        self.engine = engine

    def run(self, max_trades: int = 1000) -> dict[str, Any]:
        required = self.engine.REQUIRED_TIMEFRAMES

        for tf in required:
            if tf not in self.engine.data:
                return {"error": f"Missing {tf} data."}

        for tf in required:
            self.engine.data[tf] = self.engine.indicators(
                self.engine.data[tf]
            )

        df15 = self.engine.data["15m"]

        returns: list[float] = []
        trades: list[dict[str, Any]] = []

        in_trade = False
        trade: dict[str, Any] | None = None

        start = self.engine.config.ema_slow + 20

        for i in range(start, len(df15) - 1):
            if len(trades) >= max_trades:
                break

            current = df15.iloc[i]
            timestamp = current["Timestamp"]

            original = self.engine.data
            local: dict[str, pd.DataFrame] = {}

            for tf in required:
                frame = original[tf]
                frame = frame.loc[
                    frame["Timestamp"] <= timestamp
                ].copy()

                if len(frame) < 220:
                    local = {}
                    break

                local[tf] = frame

            if not local:
                continue

            self.engine.data = local

            try:
                result = self.engine.analyze()
            except Exception:
                result = {"signal": "NEUTRAL"}
            finally:
                self.engine.data = original

            # ---------------------------------------------------------
            # Existing trade management
            # ---------------------------------------------------------

            if in_trade and trade is not None:
                direction = trade["direction"]
                sl = trade["sl"]
                tp = trade["tp"]

                hit_sl = (
                    current["Low"] <= sl
                    if direction == "BUY"
                    else current["High"] >= sl
                )

                hit_tp = (
                    current["High"] >= tp
                    if direction == "BUY"
                    else current["Low"] <= tp
                )

                if hit_sl and hit_tp:
                    r_value = -1.0

                    returns.append(r_value)
                    trades.append({
                        "timestamp": timestamp,
                        "direction": direction,
                        "R": r_value,
                        "result": "AMBIGUOUS_STOP_FIRST",
                    })

                    in_trade = False
                    trade = None
                    continue

                if hit_sl:
                    r_value = -1.0

                    returns.append(r_value)
                    trades.append({
                        "timestamp": timestamp,
                        "direction": direction,
                        "R": r_value,
                        "result": "LOSS",
                    })

                    in_trade = False
                    trade = None
                    continue

                if hit_tp:
                    r_value = self.engine.config.reward_risk

                    returns.append(r_value)
                    trades.append({
                        "timestamp": timestamp,
                        "direction": direction,
                        "R": r_value,
                        "result": "WIN",
                    })

                    in_trade = False
                    trade = None
                    continue

            # ---------------------------------------------------------
            # New signal
            # ---------------------------------------------------------

            if (
                not in_trade
                and result.get("signal") in ("BUY", "SELL")
            ):
                score = float(result.get("score", 0.0))

                if score < self.engine.config.minimum_score:
                    continue

                tr = result["trade"]

                in_trade = True
                trade = {
                    "direction": result["signal"],
                    "entry": tr["entry"],
                    "sl": tr["stop"],
                    "tp": tr["tp"],
                }

        statistics = ExcoraPerformance.statistics(returns)

        return {
            "statistics": statistics,
            "returns": returns,
            "trades": trades,
        }


# ====================================================================
# WALK FORWARD
# ====================================================================

class ExcoraWalkForward:
    @staticmethod
    def split(
        df: pd.DataFrame,
        train_ratio: float = 0.70,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if len(df) < 100:
            raise ValueError("Insufficient data.")

        if not 0.50 <= train_ratio <= 0.90:
            raise ValueError(
                "train_ratio must be between 0.50 and 0.90."
            )

        split = int(len(df) * train_ratio)

        train = df.iloc[:split].copy()
        test = df.iloc[split:].copy()

        return train, test


# ====================================================================
# DISPLAY
# ====================================================================

def print_result(
    symbol: str,
    result: dict[str, Any],
) -> None:
    print()
    print("=" * 90)
    print(f"EXCORA QUANT MTF | {symbol}")
    print("=" * 90)

    signal = result.get("signal", "NEUTRAL")

    print(f"SIGNAL        : {signal}")

    if signal == "NEUTRAL":
        print(
            f"REASON        : "
            f"{result.get('reason', 'N/A')}"
        )

        if "score" in result:
            print(
                f"SCORE         : "
                f"{result['score']:.2f}/100"
            )

        print("=" * 90)
        return

    print(f"SCORE         : {result['score']:.2f}/100")
    print(f"GRADE         : {result['grade']}")
    print(
        f"1D TREND      : "
        f"{result['trend_1d']['trend']}"
    )
    print(
        f"4H TREND      : "
        f"{result['trend_4h']['trend']}"
    )
    print(
        f"1D STRUCTURE  : "
        f"{result['structure_1d']['structure']}"
    )
    print(
        f"4H STRUCTURE  : "
        f"{result['structure_4h']['structure']}"
    )
    print(
        f"1H STRUCTURE  : "
        f"{result['structure_1h']['structure']}"
    )
    print(
        f"LIQUIDITY     : "
        f"{result['liquidity']['type']}"
    )
    print(
        f"DISPLACEMENT  : "
        f"{'YES' if result['displacement'] else 'NO'}"
    )
    print(
        f"FVG           : "
        f"{'YES' if result['fvg'] else 'NO'}"
    )
    print(
        f"ORDER BLOCK   : "
        f"{'YES' if result['order_block'] else 'NO'}"
    )
    print(f"REGIME        : {result['regime']}")
    print(f"ATR           : {result['atr']:.8f}")
    print(f"ATR %         : {result['atr_pct']:.3f}%")
    print(
        f"REL VOLUME    : "
        f"{result['relative_volume']:.2f}"
    )
    print(f"VWAP          : {result['vwap']:.8f}")
    print(
        f"EMA SEP       : "
        f"{result['ema_separation_atr']:.3f} ATR"
    )
    print(
        f"EMA SLOPE     : "
        f"{result['ema_slope_atr']:.3f} ATR"
    )
    print(
        f"MOMENTUM      : "
        f"{result['roc5']:.3f}%"
    )

    trade = result["trade"]

    print()
    print("---------------- TRADE PLAN ----------------")
    print(f"ENTRY         : {trade['entry']:.8f}")
    print(f"STOP LOSS     : {trade['stop']:.8f}")
    print(f"TAKE PROFIT   : {trade['tp']:.8f}")
    print(f"RISK          : ${trade['risk_usd']:.4f}")
    print(
        f"POSITION SIZE : "
        f"{trade['quantity']:.8f}"
    )
    print(
        f"NOTIONAL      : "
        f"${trade['notional']:.4f}"
    )
    print(
        f"STOP DISTANCE : "
        f"{trade['risk_distance_pct']:.3f}%"
    )
    print(f"RR            : 1:{trade['rr']:.2f}")
    print("=" * 90)


# ====================================================================
# MAIN
# ====================================================================

def main() -> None:
    symbols = [
        "BTC/USDT:USDT",
        "ETH/USDT:USDT",
        "SOL/USDT:USDT",
        "XRP/USDT:USDT",
    ]

    config = ExcoraConfig(
        balance=100.0,
        risk_percent=1.0,
        reward_risk=3.0,
        minimum_score=75.0,
        candles=350,
        scan_interval=120,
    )

    telegram = TelegramNotifier(
        token=os.getenv("EXCORA_TELEGRAM_TOKEN", ""),
        chat_id=os.getenv("EXCORA_TELEGRAM_CHAT_ID", ""),
    )

    print("=" * 90)
    print("🏛 EXCORA QUANT MTF MASTER")
    print("1D → 4H → 1H → 15M")
    print(
        "EMA + STRUCTURE + LIQUIDITY + "
        "MSS/CHoCH + FVG + OB + VWAP + "
        "VOLUME PROFILE + ATR"
    )
    print("REAL SCORE 0-100")
    print("RISK 1% | RR 1:3")
    print("SIGNAL ONLY — NO REAL ORDERS")
    print("TELEGRAM ISOLATED — NO TELEGRAM LOGIC IN ENGINE")
    print("=" * 90)

    engines = {
        symbol: ExcoraQuantMTFMaster(
            symbol=symbol,
            config=config,
        )
        for symbol in symbols
    }

    while True:
        scan_time = datetime.now(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

        print()
        print("=" * 90)
        print(f"🔄 EXCORA MARKET SCAN | {scan_time}")
        print("=" * 90)

        for symbol, engine in engines.items():
            try:
                result = engine.scan()

                print_result(
                    symbol,
                    result,
                )

                if result.get("signal") in ("BUY", "SELL"):
                    telegram.send_signal(
                        symbol,
                        result,
                    )

            except KeyboardInterrupt:
                raise

            except Exception as exc:
                logger.exception(
                    "ENGINE ERROR | %s | %s",
                    symbol,
                    exc,
                )

        print()
        print(
            f"⏳ Next scan in "
            f"{config.scan_interval} seconds..."
        )
        print("=" * 90)

        try:
            time.sleep(config.scan_interval)
        except KeyboardInterrupt:
            print("\n🛑 EXCORA STOPPED")
            break


if __name__ == "__main__":
    main()
