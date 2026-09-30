"""
=================================================================
                    EXCORA V10
            INSTITUTIONAL QUANT SIGNAL CORE
=================================================================

ASSETS:
    ETH/USDT
    XRP/USDT
    AVAX/USDT
    DOGE/USDT

TIMEFRAME ARCHITECTURE:

    1D  -> Macro Trend
    4H  -> Market Structure / Context
    15M -> Liquidity / MSS / FVG / OB / Entry
    5M  -> 6H Volume Profile

CORE:

    EMA50
    EMA200
    ATR
    Relative Volume
    Daily VWAP

SMC:

    Swing High
    Swing Low
    Liquidity Sweep
    MSS / BOS
    FVG
    Order Block

VOLUME PROFILE:

    6H
    POC
    VAH
    VAL
    HVN
    LVN

RISK:

    Capital = $100
    Risk = 1%
    Maximum risk = $1
    Target = 1:3
    Maximum notional = 100% capital

SIGNAL:

    Minimum score = 82/100

ANTI DUPLICATION:

    SQLite persistent signal database
    Symbol + 15M candle + direction
    Setup fingerprint

IMPORTANT:

    Signal engine only.
    No automatic order execution.
=================================================================
"""

import os
import time
import math
import sqlite3
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import ccxt
import numpy as np
import pandas as pd
import requests


# ==============================================================
# CONFIGURATION
# ==============================================================

@dataclass
class Config:

    # ----------------------------------------------------------
    # CAPITAL
    # ----------------------------------------------------------

    capital: float = 100.0

    risk_per_trade_pct: float = 1.0

    max_notional_pct: float = 100.0

    minimum_score: int = 82

    minimum_rr: float = 3.0

    # ----------------------------------------------------------
    # DAILY RISK
    # ----------------------------------------------------------

    max_daily_loss_pct: float = 3.0

    max_consecutive_losses: int = 3

    # ----------------------------------------------------------
    # EMA
    # ----------------------------------------------------------

    ema_fast: int = 50
    ema_slow: int = 200

    # ----------------------------------------------------------
    # ATR
    # ----------------------------------------------------------

    atr_period: int = 14

    sl_atr_buffer: float = 0.20

    # ----------------------------------------------------------
    # MARKET STRUCTURE
    # ----------------------------------------------------------

    swing_left: int = 3
    swing_right: int = 3

    # ----------------------------------------------------------
    # VOLUME
    # ----------------------------------------------------------

    volume_period: int = 20

    strong_volume_ratio: float = 1.50

    # ----------------------------------------------------------
    # 6H VOLUME PROFILE
    # ----------------------------------------------------------

    vp_bins: int = 120

    vp_value_area: float = 0.70

    vp_hours: int = 6

    m5_limit: int = 1000

    # ----------------------------------------------------------
    # DATA
    # ----------------------------------------------------------

    d1_limit: int = 300

    h4_limit: int = 300

    m15_limit: int = 300

    # ----------------------------------------------------------
    # SCANNER
    # ----------------------------------------------------------

    scan_interval_seconds: int = 60

    # ----------------------------------------------------------
    # SYMBOLS
    # ----------------------------------------------------------

    symbols = (
        "ETH/USDT",
        "XRP/USDT",
        "AVAX/USDT",
        "DOGE/USDT",
    )

    # ----------------------------------------------------------
    # DATABASE
    # ----------------------------------------------------------

    database_file: str = "excora_v10_signals.db"

    # ----------------------------------------------------------
    # LOG
    # ----------------------------------------------------------

    log_file: str = "excora_v10.log"


# ==============================================================
# LOGGING
# ==============================================================

config = Config()

logging.basicConfig(
    filename=config.log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("EXCORA_V10")


# ==============================================================
# TELEGRAM
# ==============================================================

class Telegram:

    def __init__(self):

        self.token = os.getenv(
            "8716831426:AAF9AwmGPvWw_ucFCSH7dqEhwd8VCskY4Q4",
            ""
        )

        self.chat_id = os.getenv(
            "8297464896",
            ""
        )

    def enabled(self):

        return bool(
            self.token
            and self.chat_id
        )

    def send(self, message: str):

        if not self.enabled():

            logger.warning(
                "Telegram is not configured."
            )

            return False

        url = (
            "https://api.telegram.org/"
            f"bot{self.token}/sendMessage"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=15,
            )

            if response.ok:

                return True

            logger.error(
                "Telegram HTTP %s: %s",
                response.status_code,
                response.text[:300],
            )

        except Exception as exc:

            logger.error(
                "Telegram error: %s",
                exc
            )

        return False


# ==============================================================
# SIGNAL DATABASE
# ==============================================================

class SignalDatabase:

    def __init__(self, filename):

        self.filename = filename

        self.connection = sqlite3.connect(
            filename,
            check_same_thread=False
        )

        self._create_tables()

    def _create_tables(self):

        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                symbol TEXT NOT NULL,

                candle_time TEXT NOT NULL,

                direction TEXT NOT NULL,

                fingerprint TEXT NOT NULL UNIQUE,

                score INTEGER NOT NULL,

                entry REAL NOT NULL,

                stop REAL NOT NULL,

                tp1 REAL NOT NULL,

                tp2 REAL NOT NULL,

                tp3 REAL NOT NULL,

                risk_amount REAL NOT NULL,

                quantity REAL NOT NULL,

                created_at TEXT NOT NULL

            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_symbol_candle
            ON signals(symbol, candle_time)
            """
        )

        self.connection.commit()

    @staticmethod
    def fingerprint(
        symbol,
        candle_time,
        direction,
        entry,
        stop,
        score,
    ):

        raw = (
            f"{symbol}|"
            f"{candle_time}|"
            f"{direction}|"
            f"{entry:.10f}|"
            f"{stop:.10f}|"
            f"{score}"
        )

        return hashlib.sha256(
            raw.encode()
        ).hexdigest()

    def exists(
        self,
        symbol,
        candle_time,
        direction,
        entry,
        stop,
        score,
    ):

        fp = self.fingerprint(
            symbol,
            candle_time,
            direction,
            entry,
            stop,
            score,
        )

        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM signals
            WHERE fingerprint = ?
            LIMIT 1
            """,
            (fp,),
        )

        return cursor.fetchone() is not None

    def save(self, signal):

        fp = self.fingerprint(
            signal["symbol"],
            signal["candle_time"],
            signal["direction"],
            signal["entry"],
            signal["stop"],
            signal["score"],
        )

        cursor = self.connection.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO signals (
                    symbol,
                    candle_time,
                    direction,
                    fingerprint,
                    score,
                    entry,
                    stop,
                    tp1,
                    tp2,
                    tp3,
                    risk_amount,
                    quantity,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal["symbol"],
                    signal["candle_time"],
                    signal["direction"],
                    fp,
                    signal["score"],
                    signal["entry"],
                    signal["stop"],
                    signal["tp1"],
                    signal["tp2"],
                    signal["tp3"],
                    signal["risk_amount"],
                    signal["quantity"],
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
                ),
            )

            self.connection.commit()

            return True

        except sqlite3.IntegrityError:

            return False


# ==============================================================
# MARKET DATA
# ==============================================================

class MarketData:

    def __init__(self):

        self.exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot"
            }
        })

    def fetch(
        self,
        symbol,
        timeframe,
        limit,
        retries=3,
    ):

        for attempt in range(retries):

            try:

                raw = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    limit=limit,
                )

                if not raw:

                    return pd.DataFrame()

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

                df.set_index(
                    "Timestamp",
                    inplace=True,
                )

                df = df.astype(float)

                df = df[
                    ~df.index.duplicated(
                        keep="last"
                    )
                ]

                return df

            except Exception as exc:

                logger.warning(
                    "Fetch %s %s attempt %s/%s: %s",
                    symbol,
                    timeframe,
                    attempt + 1,
                    retries,
                    exc,
                )

                time.sleep(
                    1.5 * (attempt + 1)
                )

        return pd.DataFrame()


# ==============================================================
# INDICATORS
# ==============================================================

class Indicators:

    @staticmethod
    def add_ema(df):

        df = df.copy()

        df["EMA50"] = (
            df["Close"]
            .ewm(
                span=50,
                adjust=False
            )
            .mean()
        )

        df["EMA200"] = (
            df["Close"]
            .ewm(
                span=200,
                adjust=False
            )
            .mean()
        )

        return df

    @staticmethod
    def add_atr(df):

        df = df.copy()

        previous_close = (
            df["Close"].shift(1)
        )

        tr = pd.concat(
            [
                df["High"] - df["Low"],

                (
                    df["High"]
                    - previous_close
                ).abs(),

                (
                    df["Low"]
                    - previous_close
                ).abs(),
            ],
            axis=1,
        ).max(axis=1)

        df["TR"] = tr

        df["ATR"] = (
            tr.rolling(
                config.atr_period
            ).mean()
        )

        return df

    @staticmethod
    def add_relative_volume(df):

        df = df.copy()

        df["VolumeMA"] = (
            df["Volume"]
            .rolling(
                config.volume_period
            )
            .mean()
        )

        df["VolumeRatio"] = (
            df["Volume"]
            /
            df["VolumeMA"]
            .replace(0, np.nan)
        )

        return df

    @staticmethod
    def add_daily_vwap(df):

        df = df.copy()

        typical_price = (
            df["High"]
            + df["Low"]
            + df["Close"]
        ) / 3.0

        tpv = (
            typical_price
            * df["Volume"]
        )

        session = df.index.normalize()

        cumulative_tpv = (
            tpv.groupby(session)
            .cumsum()
        )

        cumulative_volume = (
            df["Volume"]
            .groupby(session)
            .cumsum()
        )

        df["VWAP"] = (
            cumulative_tpv
            /
            cumulative_volume.replace(
                0,
                np.nan
            )
        )

        return df

    @staticmethod
    def prepare(df):

        df = Indicators.add_ema(df)

        df = Indicators.add_atr(df)

        df = Indicators.add_relative_volume(df)

        df = Indicators.add_daily_vwap(df)

        return df


# ==============================================================
# MARKET STRUCTURE
# ==============================================================

class MarketStructure:

    @staticmethod
    def swings(
        df,
        left=3,
        right=3,
    ):

        highs = []

        lows = []

        if len(df) < (
            left
            + right
            + 5
        ):

            return highs, lows

        for i in range(
            left,
            len(df) - right
        ):

            high = df["High"].iloc[i]

            low = df["Low"].iloc[i]

            left_highs = (
                df["High"]
                .iloc[i-left:i]
            )

            right_highs = (
                df["High"]
                .iloc[
                    i+1:i+right+1
                ]
            )

            left_lows = (
                df["Low"]
                .iloc[i-left:i]
            )

            right_lows = (
                df["Low"]
                .iloc[
                    i+1:i+right+1
                ]
            )

            if (
                high > left_highs.max()
                and
                high > right_highs.max()
            ):

                highs.append(
                    (
                        df.index[i],
                        float(high)
                    )
                )

            if (
                low < left_lows.min()
                and
                low < right_lows.min()
            ):

                lows.append(
                    (
                        df.index[i],
                        float(low)
                    )
                )

        return highs, lows

    @staticmethod
    def trend(df):

        latest = df.iloc[-1]

        if (
            latest["Close"]
            > latest["EMA50"]
            > latest["EMA200"]
        ):

            return "BULLISH"

        if (
            latest["Close"]
            < latest["EMA50"]
            < latest["EMA200"]
        ):

            return "BEARISH"

        return "NEUTRAL"

    @staticmethod
    def bias(df):

        highs, lows = (
            MarketStructure.swings(
                df,
                config.swing_left,
                config.swing_right
            )
        )

        if (
            len(highs) < 2
            or len(lows) < 2
        ):

            return "NEUTRAL", None

        h1 = highs[-2][1]
        h2 = highs[-1][1]

        l1 = lows[-2][1]
        l2 = lows[-1][1]

        if (
            h2 > h1
            and l2 > l1
        ):

            return "BULLISH", {
                "high": h2,
                "low": l2,
            }

        if (
            h2 < h1
            and l2 < l1
        ):

            return "BEARISH", {
                "high": h2,
                "low": l2,
            }

        return "NEUTRAL", {
            "high": h2,
            "low": l2,
        }


# ==============================================================
# LIQUIDITY
# ==============================================================

class Liquidity:

    @staticmethod
    def detect(df):

        highs, lows = (
            MarketStructure.swings(
                df,
                3,
                3
            )
        )

        if (
            len(highs) < 2
            or len(lows) < 2
        ):

            return {
                "bullish_sweep": False,
                "bearish_sweep": False,
                "sweep_low": None,
                "sweep_high": None,
            }

        previous_high = highs[-2][1]

        previous_low = lows[-2][1]

        latest = df.iloc[-1]

        bullish = (
            latest["Low"]
            < previous_low
            and
            latest["Close"]
            > previous_low
        )

        bearish = (
            latest["High"]
            > previous_high
            and
            latest["Close"]
            < previous_high
        )

        return {
            "bullish_sweep": bool(bullish),
            "bearish_sweep": bool(bearish),
            "sweep_low": previous_low,
            "sweep_high": previous_high,
        }


# ==============================================================
# MSS / BOS
# ==============================================================

class StructureTrigger:

    @staticmethod
    def detect(df, direction):

        highs, lows = (
            MarketStructure.swings(
                df,
                2,
                2
            )
        )

        if not highs or not lows:

            return False

        latest_close = (
            df["Close"].iloc[-1]
        )

        if direction == "BUY":

            return bool(
                latest_close
                > highs[-1][1]
            )

        if direction == "SELL":

            return bool(
                latest_close
                < lows[-1][1]
            )

        return False


# ==============================================================
# FVG
# ==============================================================

class FVG:

    @staticmethod
    def latest(df, direction):

        if len(df) < 5:

            return None

        for i in range(
            len(df) - 1,
            1,
            -1
        ):

            if direction == "BUY":

                if (
                    df["Low"].iloc[i]
                    >
                    df["High"].iloc[i-2]
                ):

                    return {
                        "top":
                            float(
                                df["Low"].iloc[i]
                            ),

                        "bottom":
                            float(
                                df["High"].iloc[i-2]
                            ),

                        "mid":
                            float(
                                (
                                    df["Low"].iloc[i]
                                    +
                                    df["High"].iloc[i-2]
                                ) / 2
                            ),
                    }

            if direction == "SELL":

                if (
                    df["High"].iloc[i]
                    <
                    df["Low"].iloc[i-2]
                ):

                    return {
                        "top":
                            float(
                                df["Low"].iloc[i-2]
                            ),

                        "bottom":
                            float(
                                df["High"].iloc[i]
                            ),

                        "mid":
                            float(
                                (
                                    df["Low"].iloc[i-2]
                                    +
                                    df["High"].iloc[i]
                                ) / 2
                            ),
                    }

        return None


# ==============================================================
# ORDER BLOCK
# ==============================================================

class OrderBlock:

    @staticmethod
    def latest(
        df,
        direction
    ):

        if len(df) < 30:

            return None

        atr = df["ATR"].iloc[-1]

        if (
            not np.isfinite(atr)
            or atr <= 0
        ):

            return None

        start = max(
            10,
            len(df) - 80
        )

        for i in range(
            len(df) - 2,
            start,
            -1
        ):

            candle = df.iloc[i]

            next_candle = (
                df.iloc[i + 1]
            )

            if direction == "BUY":

                bearish = (
                    candle["Close"]
                    < candle["Open"]
                )

                displacement = (
                    next_candle["Close"]
                    - candle["High"]
                )

                if (
                    bearish
                    and displacement
                    > atr * 1.2
                ):

                    return {
                        "high":
                            float(
                                candle["Open"]
                            ),

                        "low":
                            float(
                                candle["Low"]
                            ),
                    }

            if direction == "SELL":

                bullish = (
                    candle["Close"]
                    > candle["Open"]
                )

                displacement = (
                    candle["Low"]
                    - next_candle["Close"]
                )

                if (
                    bullish
                    and displacement
                    > atr * 1.2
                ):

                    return {
                        "high":
                            float(
                                candle["High"]
                            ),

                        "low":
                            float(
                                candle["Open"]
                            ),
                    }

        return None


# ==============================================================
# INSTITUTIONAL 6H VOLUME PROFILE
# ==============================================================

class VolumeProfile6H:

    @staticmethod
    def calculate(
        df_5m,
        bins=120,
        value_area=0.70,
        hours=6,
    ):

        if (
            df_5m is None
            or df_5m.empty
        ):

            return None

        df = df_5m.copy()

        end_time = df.index[-1]

        start_time = (
            end_time
            - pd.Timedelta(
                hours=hours
            )
        )

        df = df[
            df.index > start_time
        ].copy()

        if len(df) < 20:

            return None

        price_low = float(
            df["Low"].min()
        )

        price_high = float(
            df["High"].max()
        )

        if (
            price_high
            <= price_low
        ):

            return None

        edges = np.linspace(
            price_low,
            price_high,
            bins + 1
        )

        centers = (
            edges[:-1]
            + edges[1:]
        ) / 2.0

        profile = np.zeros(
            bins,
            dtype=np.float64
        )

        # ------------------------------------------------------
        # Volume is distributed according to price overlap.
        # This is more accurate than assigning equal volume
        # to every touched bin.
        # ------------------------------------------------------

        for row in df.itertuples():

            candle_low = float(
                row.Low
            )

            candle_high = float(
                row.High
            )

            volume = float(
                row.Volume
            )

            if volume <= 0:

                continue

            if candle_high <= candle_low:

                idx = (
                    np.searchsorted(
                        edges,
                        candle_low,
                        side="right"
                    )
                    - 1
                )

                idx = max(
                    0,
                    min(
                        bins - 1,
                        idx
                    )
                )

                profile[idx] += volume

                continue

            candle_range = (
                candle_high
                - candle_low
            )

            first = max(
                0,
                np.searchsorted(
                    edges,
                    candle_low,
                    side="right"
                ) - 1
            )

            last = min(
                bins - 1,
                np.searchsorted(
                    edges,
                    candle_high,
                    side="left"
                )
            )

            for idx in range(
                first,
                last + 1
            ):

                bin_low = edges[idx]

                bin_high = edges[idx + 1]

                overlap = max(
                    0.0,
                    min(
                        candle_high,
                        bin_high
                    )
                    -
                    max(
                        candle_low,
                        bin_low
                    )
                )

                if overlap > 0:

                    profile[idx] += (
                        volume
                        *
                        overlap
                        /
                        candle_range
                    )

        total_volume = (
            profile.sum()
        )

        if total_volume <= 0:

            return None

        # ------------------------------------------------------
        # POC
        # ------------------------------------------------------

        poc_index = int(
            np.argmax(profile)
        )

        poc = float(
            centers[poc_index]
        )

        # ------------------------------------------------------
        # VALUE AREA
        # ------------------------------------------------------

        target = (
            total_volume
            * value_area
        )

        accumulated = (
            profile[poc_index]
        )

        lower = poc_index
        upper = poc_index

        while accumulated < target:

            lower_volume = (
                profile[lower - 1]
                if lower > 0
                else -1
            )

            upper_volume = (
                profile[upper + 1]
                if upper < bins - 1
                else -1
            )

            if (
                upper_volume >= lower_volume
                and
                upper < bins - 1
            ):

                upper += 1

                accumulated += (
                    profile[upper]
                )

            elif lower > 0:

                lower -= 1

                accumulated += (
                    profile[lower]
                )

            else:

                break

        val = float(
            centers[lower]
        )

        vah = float(
            centers[upper]
        )

        # ------------------------------------------------------
        # HVN / LVN
        # ------------------------------------------------------

        mean = profile.mean()

        std = profile.std()

        hvn_threshold = (
            mean + std
        )

        lvn_threshold = max(
            0,
            mean - std
        )

        hvn_indices = np.where(
            profile >= hvn_threshold
        )[0]

        lvn_indices = np.where(
            profile <= lvn_threshold
        )[0]

        hvns = [
            float(centers[i])
            for i in hvn_indices
        ]

        lvns = [
            float(centers[i])
            for i in lvn_indices
        ]

        current_price = float(
            df["Close"].iloc[-1]
        )

        # ------------------------------------------------------
        # Location
        # ------------------------------------------------------

        if current_price < val:

            location = "BELOW_VALUE"

        elif current_price > vah:

            location = "ABOVE_VALUE"

        elif current_price < poc:

            location = "LOWER_VALUE"

        elif current_price > poc:

            location = "UPPER_VALUE"

        else:

            location = "AT_POC"

        return {

            "POC": poc,

            "VAH": vah,

            "VAL": val,

            "HVNs": hvns,

            "LVNs": lvns,

            "location": location,

            "current_price":
                current_price,

            "total_volume":
                float(total_volume),

            "profile": profile,

            "prices": centers,
        }


# ==============================================================
# VOLUME PROFILE SIGNAL
# ==============================================================

class VolumeProfileSignal:

    @staticmethod
    def evaluate(
        price,
        vp,
        direction
    ):

        poc = vp["POC"]

        val = vp["VAL"]

        vah = vp["VAH"]

        value_range = max(
            vah - val,
            price * 0.0001
        )

        tolerance = (
            value_range * 0.10
        )

        if direction == "BUY":

            if price <= val + tolerance:

                return (
                    10,
                    "VP_VAL_LONG"
                )

            if (
                price > val
                and price < poc
            ):

                return (
                    8,
                    "VP_LOWER_VALUE"
                )

            if abs(
                price - poc
            ) <= tolerance:

                return (
                    5,
                    "VP_POC"
                )

            return (
                0,
                "VP_BAD_LONG_LOCATION"
            )

        if direction == "SELL":

            if price >= vah - tolerance:

                return (
                    10,
                    "VP_VAH_SHORT"
                )

            if (
                price < vah
                and price > poc
            ):

                return (
                    8,
                    "VP_UPPER_VALUE"
                )

            if abs(
                price - poc
            ) <= tolerance:

                return (
                    5,
                    "VP_POC"
                )

            return (
                0,
                "VP_BAD_SHORT_LOCATION"
            )

        return (
            0,
            "VP_NEUTRAL"
        )


# ==============================================================
# DAILY TREND
# ==============================================================

class DailyTrend:

    @staticmethod
    def evaluate(
        df,
        direction
    ):

        latest = df.iloc[-1]

        price = latest["Close"]

        ema50 = latest["EMA50"]

        ema200 = latest["EMA200"]

        if direction == "BUY":

            if (
                price > ema200
                and
                ema50 > ema200
            ):

                return True, 25, "D1_BULLISH"

        if direction == "SELL":

            if (
                price < ema200
                and
                ema50 < ema200
            ):

                return True, 25, "D1_BEARISH"

        return (
            False,
            0,
            "D1_GATE_FAILED"
        )


# ==============================================================
# 4H CONTEXT
# ==============================================================

class FourHourContext:

    @staticmethod
    def evaluate(
        df,
        direction
    ):

        trend = (
            MarketStructure.trend(df)
        )

        structure, _ = (
            MarketStructure.bias(df)
        )

        latest = df.iloc[-1]

        if direction == "BUY":

            ema_alignment = (
                latest["Close"]
                >
                latest["EMA50"]
                >
                latest["EMA200"]
            )

            valid = (
                trend == "BULLISH"
                and
                structure == "BULLISH"
                and
                ema_alignment
            )

        else:

            ema_alignment = (
                latest["Close"]
                <
                latest["EMA50"]
                <
                latest["EMA200"]
            )

            valid = (
                trend == "BEARISH"
                and
                structure == "BEARISH"
                and
                ema_alignment
            )

        if valid:

            return (
                True,
                20,
                "4H_FULL_ALIGNMENT"
            )

        return (
            False,
            0,
            "4H_GATE_FAILED"
        )


# ==============================================================
# SMC EXECUTION
# ==============================================================

class SMC:

    @staticmethod
    def evaluate(
        df,
        direction
    ):

        liquidity = (
            Liquidity.detect(df)
        )

        if direction == "BUY":

            sweep = (
                liquidity["bullish_sweep"]
            )

        else:

            sweep = (
                liquidity["bearish_sweep"]
            )

        mss = (
            StructureTrigger.detect(
                df,
                direction
            )
        )

        fvg = (
            FVG.latest(
                df,
                direction
            )
        )

        ob = (
            OrderBlock.latest(
                df,
                direction
            )
        )

        latest = df.iloc[-1]

        volume_confirmed = (
            np.isfinite(
                latest["VolumeRatio"]
            )
            and
            latest["VolumeRatio"]
            >= config.strong_volume_ratio
        )

        return {

            "liquidity":
                liquidity,

            "sweep":
                sweep,

            "mss":
                mss,

            "fvg":
                fvg,

            "ob":
                ob,

            "volume":
                volume_confirmed,
        }


# ==============================================================
# SCORE ENGINE
# ==============================================================

class ScoreEngine:

    @staticmethod
    def evaluate(
        direction,
        d1,
        h4,
        m15,
        vp
    ):

        score = 0

        reasons = []

        # ------------------------------------------------------
        # 1 — DAILY = 25
        # ------------------------------------------------------

        ok, points, reason = (
            DailyTrend.evaluate(
                d1,
                direction
            )
        )

        if not ok:

            return {
                "valid": False,
                "score": 0,
                "reasons": [
                    "D1_GATE_FAILED"
                ]
            }

        score += points

        reasons.append(reason)

        # ------------------------------------------------------
        # 2 — 4H = 20
        # ------------------------------------------------------

        ok, points, reason = (
            FourHourContext.evaluate(
                h4,
                direction
            )
        )

        if not ok:

            return {
                "valid": False,
                "score": score,
                "reasons": [
                    "4H_GATE_FAILED"
                ]
            }

        score += points

        reasons.append(reason)

        # ------------------------------------------------------
        # 3 — SMC
        # ------------------------------------------------------

        smc = (
            SMC.evaluate(
                m15,
                direction
            )
        )

        # ------------------------------------------------------
        # 3A — LIQUIDITY = 15
        # ------------------------------------------------------

        if not smc["sweep"]:

            return {
                "valid": False,
                "score": score,
                "reasons": [
                    "LIQUIDITY_GATE_FAILED"
                ]
            }

        score += 15

        reasons.append(
            "LIQUIDITY_SWEEP"
        )

        # ------------------------------------------------------
        # 3B — MSS/BOS = 15
        # ------------------------------------------------------

        if not smc["mss"]:

            return {
                "valid": False,
                "score": score,
                "reasons": [
                    "MSS_BOS_GATE_FAILED"
                ]
            }

        score += 15

        reasons.append(
            "MSS_BOS_CONFIRMED"
        )

        # ------------------------------------------------------
        # 4 — VOLUME PROFILE = 10
        # ------------------------------------------------------

        price = float(
            m15["Close"].iloc[-1]
        )

        vp_points, vp_reason = (
            VolumeProfileSignal.evaluate(
                price,
                vp,
                direction
            )
        )

        score += vp_points

        reasons.append(
            vp_reason
        )

        # ------------------------------------------------------
        # 5 — FVG / OB = 5
        # ------------------------------------------------------

        if (
            smc["fvg"] is not None
            or
            smc["ob"] is not None
        ):

            score += 5

            reasons.append(
                "FVG_OR_ORDER_BLOCK"
            )

        # ------------------------------------------------------
        # 6 — RELATIVE VOLUME = 5
        # ------------------------------------------------------

        if smc["volume"]:

            score += 5

            reasons.append(
                "RELATIVE_VOLUME"
            )

        # ------------------------------------------------------
        # 7 — VWAP = 5
        # ------------------------------------------------------

        latest = m15.iloc[-1]

        if direction == "BUY":

            if (
                np.isfinite(
                    latest["VWAP"]
                )
                and
                latest["Close"]
                > latest["VWAP"]
            ):

                score += 5

                reasons.append(
                    "VWAP_BULLISH"
                )

        else:

            if (
                np.isfinite(
                    latest["VWAP"]
                )
                and
                latest["Close"]
                < latest["VWAP"]
            ):

                score += 5

                reasons.append(
                    "VWAP_BEARISH"
                )

        return {

            "valid":
                score >= config.minimum_score,

            "score":
                score,

            "reasons":
                reasons,

            "smc":
                smc,
        }


# ==============================================================
# STOP ENGINE
# ==============================================================

class StopEngine:

    @staticmethod
    def calculate(
        df,
        direction,
        liquidity
    ):

        latest = df.iloc[-1]

        entry = float(
            latest["Close"]
        )

        atr = float(
            latest["ATR"]
        )

        if (
            not np.isfinite(atr)
            or atr <= 0
        ):

            return None

        if direction == "BUY":

            reference = (
                liquidity["sweep_low"]
            )

            if reference is None:

                reference = float(
                    df["Low"]
                    .tail(20)
                    .min()
                )

            stop = (
                reference
                -
                atr * config.sl_atr_buffer
            )

            if stop >= entry:

                return None

            return stop

        reference = (
            liquidity["sweep_high"]
        )

        if reference is None:

            reference = float(
                df["High"]
                .tail(20)
                .max()
            )

        stop = (
            reference
            +
            atr * config.sl_atr_buffer
        )

        if stop <= entry:

            return None

        return stop


# ==============================================================
# RISK ENGINE
# ==============================================================

class RiskEngine:

    @staticmethod
    def calculate(
        entry,
        stop,
        direction
    ):

        if (
            not np.isfinite(entry)
            or
            not np.isfinite(stop)
        ):

            return None

        if direction == "BUY":

            distance = (
                entry - stop
            )

        else:

            distance = (
                stop - entry
            )

        if distance <= 0:

            return None

        risk_amount = (
            config.capital
            *
            config.risk_per_trade_pct
            /
            100.0
        )

        # $100 capital × 1% = $1 maximum risk.

        quantity = (
            risk_amount
            /
            distance
        )

        max_notional = (
            config.capital
            *
            config.max_notional_pct
            /
            100.0
        )

        notional = (
            quantity
            *
            entry
        )

        if notional > max_notional:

            quantity = (
                max_notional
                /
                entry
            )

            notional = (
                quantity
                *
                entry
            )

            risk_amount = (
                distance
                *
                quantity
            )

        # ------------------------------------------------------
        # EXACT 1:3 TARGET
        # ------------------------------------------------------

        tp1 = (
            entry + distance
            if direction == "BUY"
            else entry - distance
        )

        tp2 = (
            entry + distance * 2
            if direction == "BUY"
            else entry - distance * 2
        )

        tp3 = (
            entry + distance * 3
            if direction == "BUY"
            else entry - distance * 3
        )

        rr = (
            abs(tp3 - entry)
            /
            distance
        )

        if rr < config.minimum_rr:

            return None

        return {

            "entry":
                entry,

            "stop":
                stop,

            "tp1":
                tp1,

            "tp2":
                tp2,

            "tp3":
                tp3,

            "distance":
                distance,

            "risk_amount":
                risk_amount,

            "quantity":
                quantity,

            "notional":
                notional,

            "rr":
                rr,
        }


# ==============================================================
# SIGNAL FORMATTER
# ==============================================================

class SignalFormatter:

    @staticmethod
    def telegram(signal):

        direction = (
            "🟢 BUY / LONG"
            if signal["direction"] == "BUY"
            else
            "🔴 SELL / SHORT"
        )

        reasons = "\n".join(
            f"• {r}"
            for r in signal["reasons"]
        )

        vp = signal["vp"]

        return f"""
<b>🏛 EXCORA V10 — INSTITUTIONAL SIGNAL</b>

━━━━━━━━━━━━━━━━━━━━

<b>Asset:</b> {signal["symbol"]}

<b>Direction:</b>
{direction}

<b>Score:</b>
🔥 <b>{signal["score"]}/100</b>

━━━━━━━━━━━━━━━━━━━━

<b>📍 ENTRY</b>
<code>{signal["entry"]:.8f}</code>

<b>🛑 STOP LOSS</b>
<code>{signal["stop"]:.8f}</code>

<b>🎯 TP1 — 1R</b>
<code>{signal["tp1"]:.8f}</code>

<b>🎯 TP2 — 2R</b>
<code>{signal["tp2"]:.8f}</code>

<b>🎯 TP3 — 3R</b>
<code>{signal["tp3"]:.8f}</code>

━━━━━━━━━━━━━━━━━━━━

<b>💰 CAPITAL</b>
${config.capital:.2f}

<b>🛡 RISK</b>
${signal["risk_amount"]:.4f}

<b>📦 POSITION</b>
{signal["quantity"]:.8f}

<b>💵 NOTIONAL</b>
${signal["notional"]:.4f}

<b>⚖️ R:R</b>
1:{signal["rr"]:.2f}

━━━━━━━━━━━━━━━━━━━━

<b>📊 6H VOLUME PROFILE</b>

POC:
<code>{vp["POC"]:.8f}</code>

VAL:
<code>{vp["VAL"]:.8f}</code>

VAH:
<code>{vp["VAH"]:.8f}</code>

Location:
<b>{vp["location"]}</b>

━━━━━━━━━━━━━━━━━━━━

<b>🧠 CONFLUENCE</b>

{reasons}

━━━━━━━━━━━━━━━━━━━━

<b>⏱ 15M CLOSED CANDLE</b>

{signal["candle_time"]}

━━━━━━━━━━━━━━━━━━━━

<b>⚠️ SYSTEM</b>

Risk engine active.
Maximum theoretical risk = 1%.
Target architecture = 1:3.
No duplicate signal.

<i>EXCORA V10 Quant Core</i>
"""


# ==============================================================
# EXCORA V10 CORE
# ==============================================================

class EXCORA:

    def __init__(self):

        self.data = MarketData()

        self.telegram = Telegram()

        self.database = SignalDatabase(
            config.database_file
        )

    # ----------------------------------------------------------
    # Analyze one symbol
    # ----------------------------------------------------------

    def analyze(self, symbol):

        try:

            logger.info(
                "Analyzing %s",
                symbol
            )

            # ==================================================
            # DATA
            # ==================================================

            d1 = self.data.fetch(
                symbol,
                "1d",
                config.d1_limit
            )

            h4 = self.data.fetch(
                symbol,
                "4h",
                config.h4_limit
            )

            m15 = self.data.fetch(
                symbol,
                "15m",
                config.m15_limit
            )

            m5 = self.data.fetch(
                symbol,
                "5m",
                config.m5_limit
            )

            if any(
                df.empty
                for df in [
                    d1,
                    h4,
                    m15,
                    m5
                ]
            ):

                return None

            # ==================================================
            # REMOVE OPEN CANDLES
            # ==================================================

            d1 = d1.iloc[:-1].copy()

            h4 = h4.iloc[:-1].copy()

            m15 = m15.iloc[:-1].copy()

            m5 = m5.iloc[:-1].copy()

            # ==================================================
            # INDICATORS
            # ==================================================

            d1 = Indicators.prepare(d1)

            h4 = Indicators.prepare(h4)

            m15 = Indicators.prepare(m15)

            # ==================================================
            # 6H VOLUME PROFILE
            # ==================================================

            vp = (
                VolumeProfile6H.calculate(
                    m5,
                    bins=config.vp_bins,
                    value_area=
                        config.vp_value_area,
                    hours=config.vp_hours,
                )
            )

            if vp is None:

                return None

            candidates = []

            # ==================================================
            # BOTH DIRECTIONS
            # ==================================================

            for direction in (
                "BUY",
                "SELL"
            ):

                score_result = (
                    ScoreEngine.evaluate(
                        direction,
                        d1,
                        h4,
                        m15,
                        vp
                    )
                )

                if not score_result["valid"]:

                    continue

                # ============================================
                # LIQUIDITY
                # ============================================

                smc = score_result["smc"]

                liquidity = (
                    smc["liquidity"]
                )

                # ============================================
                # STOP
                # ============================================

                stop = (
                    StopEngine.calculate(
                        m15,
                        direction,
                        liquidity
                    )
                )

                if stop is None:

                    continue

                entry = float(
                    m15["Close"].iloc[-1]
                )

                # ============================================
                # RISK
                # ============================================

                risk = (
                    RiskEngine.calculate(
                        entry,
                        stop,
                        direction
                    )
                )

                if risk is None:

                    continue

                # ============================================
                # SIGNAL
                # ============================================

                candle_time = (
                    m15.index[-1]
                    .isoformat()
                )

                signal = {

                    "symbol":
                        symbol,

                    "direction":
                        direction,

                    "score":
                        score_result["score"],

                    "entry":
                        risk["entry"],

                    "stop":
                        risk["stop"],

                    "tp1":
                        risk["tp1"],

                    "tp2":
                        risk["tp2"],

                    "tp3":
                        risk["tp3"],

                    "quantity":
                        risk["quantity"],

                    "risk_amount":
                        risk["risk_amount"],

                    "notional":
                        risk["notional"],

                    "rr":
                        risk["rr"],

                    "reasons":
                        score_result["reasons"],

                    "vp":
                        {
                            "POC":
                                vp["POC"],

                            "VAL":
                                vp["VAL"],

                            "VAH":
                                vp["VAH"],

                            "location":
                                vp["location"],
                        },

                    "candle_time":
                        candle_time,
                }

                candidates.append(
                    signal
                )

            # ==================================================
            # NO SIGNAL
            # ==================================================

            if not candidates:

                return None

            # ==================================================
            # BEST SCORE
            # ==================================================

            candidates.sort(
                key=lambda x: (
                    x["score"],
                    x["rr"]
                ),
                reverse=True
            )

            return candidates[0]

        except Exception as exc:

            logger.exception(
                "Analysis error %s: %s",
                symbol,
                exc
            )

            return None

    # ----------------------------------------------------------
    # Process signal
    # ----------------------------------------------------------

    def process_signal(
        self,
        signal
    ):

        if signal is None:

            return

        # ======================================================
        # DATABASE DUPLICATION CHECK
        # ======================================================

        already_exists = (
            self.database.exists(
                symbol=signal["symbol"],
                candle_time=
                    signal["candle_time"],
                direction=
                    signal["direction"],
                entry=
                    signal["entry"],
                stop=
                    signal["stop"],
                score=
                    signal["score"],
            )
        )

        if already_exists:

            logger.info(
                "%s %s -> DUPLICATE BLOCKED",
                signal["symbol"],
                signal["direction"]
            )

            return

        # ======================================================
        # SAVE BEFORE TELEGRAM
        # ======================================================

        saved = (
            self.database.save(
                signal
            )
        )

        if not saved:

            logger.info(
                "Duplicate database insert blocked."
            )

            return

        # ======================================================
        # TELEGRAM
        # ======================================================

        message = (
            SignalFormatter.telegram(
                signal
            )
        )

        sent = (
            self.telegram.send(
                message
            )
        )

        if sent:

            logger.info(
                "%s %s SCORE=%s -> TELEGRAM SENT",
                signal["symbol"],
                signal["direction"],
                signal["score"]
            )

        else:

            logger.warning(
                "%s -> signal saved but Telegram failed",
                signal["symbol"]
            )

        # ======================================================
        # CONSOLE
        # ======================================================

        self.print_signal(
            signal
        )

    # ----------------------------------------------------------
    # Print
    # ----------------------------------------------------------

    @staticmethod
    def print_signal(signal):

        print()
        print("=" * 70)

        print(
            "EXCORA V10 INSTITUTIONAL SIGNAL"
        )

        print("=" * 70)

        print(
            f"Asset       : "
            f"{signal['symbol']}"
        )

        print(
            f"Direction   : "
            f"{signal['direction']}"
        )

        print(
            f"Score       : "
            f"{signal['score']}/100"
        )

        print(
            f"Entry       : "
            f"{signal['entry']:.8f}"
        )

        print(
            f"SL          : "
            f"{signal['stop']:.8f}"
        )

        print(
            f"TP1         : "
            f"{signal['tp1']:.8f}"
        )

        print(
            f"TP2         : "
            f"{signal['tp2']:.8f}"
        )

        print(
            f"TP3         : "
            f"{signal['tp3']:.8f}"
        )

        print(
            f"Risk        : "
            f"${signal['risk_amount']:.4f}"
        )

        print(
            f"Quantity    : "
            f"{signal['quantity']:.8f}"
        )

        print(
            f"Notional    : "
            f"${signal['notional']:.4f}"
        )

        print(
            f"RR          : "
            f"1:{signal['rr']:.2f}"
        )

        print(
            f"POC         : "
            f"{signal['vp']['POC']:.8f}"
        )

        print(
            f"VAL         : "
            f"{signal['vp']['VAL']:.8f}"
        )

        print(
            f"VAH         : "
            f"{signal['vp']['VAH']:.8f}"
        )

        print()

        print("CONFLUENCE:")

        for reason in signal["reasons"]:

            print(
                f"  + {reason}"
            )

        print("=" * 70)

    # ----------------------------------------------------------
    # Main scanner
    # ----------------------------------------------------------

    def run(self):

        print(
            """
==============================================================
              EXCORA V10 INSTITUTIONAL CORE
==============================================================
 CAPITAL        : $100
 RISK           : 1%
 MAX RISK       : $1
 TARGET         : 1:3
 SCORE           : >= 82/100

 TIMEFRAMES:
 1D             : Macro Trend
 4H             : Structure
 15M            : Execution
 5M             : 6H Volume Profile

 ASSETS:
 ETH / XRP / AVAX / DOGE

 TELEGRAM       : ENABLED IF ENV CONFIGURED
 DUPLICATES     : SQLITE BLOCKED
==============================================================
"""
        )

        while True:

            cycle_start = time.time()

            logger.info(
                "========== NEW SCAN =========="
            )

            for symbol in config.symbols:

                signal = (
                    self.analyze(
                        symbol
                    )
                )

                if signal is None:

                    logger.info(
                        "%s -> NO VALID SETUP",
                        symbol
                    )

                    continue

                self.process_signal(
                    signal
                )

            elapsed = (
                time.time()
                - cycle_start
            )

            sleep_time = max(
                5,
                config.scan_interval_seconds
                - elapsed
            )

            logger.info(
                "Scan completed in %.2fs | sleeping %.2fs",
                elapsed,
                sleep_time
            )

            time.sleep(
                sleep_time
            )


# ==============================================================
# ENTRY POINT
# ==============================================================

def main():

    engine = EXCORA()

    try:

        engine.run()

    except KeyboardInterrupt:

        print(
            "\nEXCORA V10 stopped."
        )

    except Exception as exc:

        logger.exception(
            "Fatal error: %s",
            exc
        )


if __name__ == "__main__":

    main()
