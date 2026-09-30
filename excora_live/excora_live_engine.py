"""
====================================================================
                    EXCORA QUANT EMA MASTER
====================================================================

                 ROBUST TRIPLE-TF SIGNAL ENGINE

Architecture:

        1D
         │
         │ Macro Trend
         ▼
        4H
         │
         │ Trend Confirmation
         ▼
        15M
         │
         ├── EMA 50/200 Crossover
         ├── EMA Separation
         ├── EMA Slope
         ├── ATR
         ├── Relative Volume
         ├── Candle Quality
         ├── Market Regime
         └── Momentum
         │
         ▼
      SIGNAL ENGINE
         │
         ▼
      SCORE ENGINE
         │
         ▼
     RISK VALIDATION
         │
         ├── 1% Account Risk
         ├── Structural SL
         ├── ATR Buffer
         ├── Minimum Stop
         ├── Maximum Stop
         └── RR 1:3
         │
         ▼
      SIGNAL QUALITY
         │
         ▼
       TELEGRAM

IMPORTANT:
    SIGNAL / SCANNER ONLY
    NO REAL ORDER EXECUTION
====================================================================
"""

import time
import logging
import requests
import ccxt
import numpy as np
import pandas as pd

from datetime import datetime, timezone


# ==================================================================
# LOGGING
# ==================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("EXCORA")


# ==================================================================
# ENGINE
# ==================================================================

class ExcoraTripleTFQuantEngine:

    def __init__(
        self,
        symbol: str,
        balance: float = 100.0,
        risk_per_trade_pct: float = 1.0,
        reward_risk: float = 3.0,
        telegram_token: str = None,
        chat_id: str = None,

        # ----------------------------------------------------------
        # Signal configuration
        # ----------------------------------------------------------

        min_score: float = 75.0,

        # EMA
        ema_fast: int = 50,
        ema_slow: int = 200,

        # ATR
        atr_period: int = 14,

        # Slope
        slope_period: int = 5,

        # Volume
        volume_period: int = 20,

        # Structure
        structure_lookback: int = 8,

        # ATR stop buffer
        atr_stop_buffer: float = 0.25,

        # Stop boundaries
        min_stop_atr: float = 0.50,
        max_stop_atr: float = 4.00,

        # Extreme volatility
        max_atr_pct: float = 8.0,

        # Minimum relative volume
        min_relative_volume: float = 0.80
    ):

        self.symbol = symbol

        self.balance = float(balance)

        self.risk_pct = float(
            risk_per_trade_pct
        )

        self.reward_risk = float(
            reward_risk
        )

        self.telegram_token = telegram_token
        self.chat_id = chat_id

        self.min_score = float(min_score)

        self.ema_fast = int(ema_fast)
        self.ema_slow = int(ema_slow)

        self.atr_period = int(atr_period)

        self.slope_period = int(
            slope_period
        )

        self.volume_period = int(
            volume_period
        )

        self.structure_lookback = int(
            structure_lookback
        )

        self.atr_stop_buffer = float(
            atr_stop_buffer
        )

        self.min_stop_atr = float(
            min_stop_atr
        )

        self.max_stop_atr = float(
            max_stop_atr
        )

        self.max_atr_pct = float(
            max_atr_pct
        )

        self.min_relative_volume = float(
            min_relative_volume
        )

        # ----------------------------------------------------------
        # Binance Futures
        # ----------------------------------------------------------

        self.exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {
                "defaultType": "future"
            }
        })

        # ----------------------------------------------------------
        # Data storage
        # ----------------------------------------------------------

        self.timeframes_data = {}

        # ----------------------------------------------------------
        # Duplicate protection
        # ----------------------------------------------------------

        self.last_signal_id = None

        # ----------------------------------------------------------
        # Last scan
        # ----------------------------------------------------------

        self.last_scan_time = None

    # ==================================================================
    # SAFE NUMBER
    # ==================================================================

    @staticmethod
    def is_valid_number(value):

        try:

            return np.isfinite(
                float(value)
            )

        except Exception:

            return False

    # ==================================================================
    # FETCH MARKET DATA
    # ==================================================================

    def fetch_live_data(
        self,
        timeframe: str,
        limit: int = 350,
        retries: int = 3
    ):

        for attempt in range(
            1,
            retries + 1
        ):

            try:

                ohlcv = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=timeframe,
                    limit=limit
                )

                if not ohlcv:

                    raise ValueError(
                        "Empty OHLCV response."
                    )

                df = pd.DataFrame(
                    ohlcv,
                    columns=[
                        "Timestamp",
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume"
                    ]
                )

                # --------------------------------------------------
                # Timestamp
                # --------------------------------------------------

                df["Timestamp"] = pd.to_datetime(
                    df["Timestamp"],
                    unit="ms",
                    utc=True
                )

                # --------------------------------------------------
                # Numeric conversion
                # --------------------------------------------------

                numeric_columns = [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ]

                for column in numeric_columns:

                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )

                # --------------------------------------------------
                # Remove invalid values
                # --------------------------------------------------

                df.dropna(
                    subset=numeric_columns,
                    inplace=True
                )

                # --------------------------------------------------
                # Remove duplicates
                # --------------------------------------------------

                df.drop_duplicates(
                    subset=["Timestamp"],
                    inplace=True
                )

                # --------------------------------------------------
                # Sort
                # --------------------------------------------------

                df.sort_values(
                    "Timestamp",
                    inplace=True
                )

                df.reset_index(
                    drop=True,
                    inplace=True
                )

                # --------------------------------------------------
                # OHLC sanity checks
                # --------------------------------------------------

                invalid_ohlc = (
                    (df["High"] < df["Low"])
                    |
                    (df["High"] < df["Open"])
                    |
                    (df["High"] < df["Close"])
                    |
                    (df["Low"] > df["Open"])
                    |
                    (df["Low"] > df["Close"])
                    |
                    (df["Volume"] < 0)
                )

                df = df[
                    ~invalid_ohlc
                ].copy()

                df.reset_index(
                    drop=True,
                    inplace=True
                )

                # --------------------------------------------------
                # Minimum history
                # --------------------------------------------------

                minimum_required = (
                    self.ema_slow + 30
                )

                if len(df) < minimum_required:

                    raise ValueError(
                        f"Insufficient candles: "
                        f"{len(df)} < "
                        f"{minimum_required}"
                    )

                # --------------------------------------------------
                # Store
                # --------------------------------------------------

                self.timeframes_data[
                    timeframe
                ] = df

                logger.info(
                    f"DATA OK | "
                    f"{self.symbol} | "
                    f"{timeframe} | "
                    f"{len(df)} candles"
                )

                return True

            except Exception as exc:

                logger.warning(
                    f"DATA RETRY "
                    f"{attempt}/{retries} | "
                    f"{self.symbol} | "
                    f"{timeframe} | "
                    f"{exc}"
                )

                if attempt < retries:

                    time.sleep(
                        2 ** (attempt - 1)
                    )

        return False

    # ==================================================================
    # INDICATORS
    # ==================================================================

    def calculate_indicators(
        self,
        df: pd.DataFrame
    ):

        df = df.copy()

        # ----------------------------------------------------------
        # EMA 50
        # ----------------------------------------------------------

        df["EMA_50"] = (
            df["Close"]
            .ewm(
                span=self.ema_fast,
                adjust=False
            )
            .mean()
        )

        # ----------------------------------------------------------
        # EMA 200
        # ----------------------------------------------------------

        df["EMA_200"] = (
            df["Close"]
            .ewm(
                span=self.ema_slow,
                adjust=False
            )
            .mean()
        )

        # ----------------------------------------------------------
        # EMA slopes
        # ----------------------------------------------------------

        df["EMA50_Slope"] = (
            df["EMA_50"]
            -
            df["EMA_50"].shift(
                self.slope_period
            )
        )

        df["EMA200_Slope"] = (
            df["EMA_200"]
            -
            df["EMA_200"].shift(
                self.slope_period
            )
        )

        # ----------------------------------------------------------
        # ATR
        # ----------------------------------------------------------

        previous_close = (
            df["Close"].shift(1)
        )

        tr1 = (
            df["High"]
            -
            df["Low"]
        )

        tr2 = (
            df["High"]
            -
            previous_close
        ).abs()

        tr3 = (
            df["Low"]
            -
            previous_close
        ).abs()

        df["TR"] = pd.concat(
            [tr1, tr2, tr3],
            axis=1
        ).max(axis=1)

        df["ATR_14"] = (
            df["TR"]
            .ewm(
                alpha=1 / self.atr_period,
                adjust=False
            )
            .mean()
        )

        # ----------------------------------------------------------
        # ATR %
        # ----------------------------------------------------------

        df["ATR_Pct"] = (
            df["ATR_14"]
            /
            df["Close"]
        ) * 100.0

        # ----------------------------------------------------------
        # Normalized EMA separation
        #
        # Distance between EMA50 and EMA200
        # relative to ATR.
        # ----------------------------------------------------------

        df["EMA_Separation_ATR"] = (
            (
                df["EMA_50"]
                -
                df["EMA_200"]
            ).abs()
            /
            df["ATR_14"].replace(
                0,
                np.nan
            )
        )

        # ----------------------------------------------------------
        # Normalized slope
        # ----------------------------------------------------------

        df["EMA50_Slope_ATR"] = (
            df["EMA50_Slope"].abs()
            /
            df["ATR_14"].replace(
                0,
                np.nan
            )
        )

        df["EMA200_Slope_ATR"] = (
            df["EMA200_Slope"].abs()
            /
            df["ATR_14"].replace(
                0,
                np.nan
            )
        )

        # ----------------------------------------------------------
        # Volume MA
        # ----------------------------------------------------------

        df["Volume_MA"] = (
            df["Volume"]
            .rolling(
                self.volume_period
            )
            .mean()
        )

        # ----------------------------------------------------------
        # Relative volume
        # ----------------------------------------------------------

        df["Relative_Volume"] = (
            df["Volume"]
            /
            df["Volume_MA"].replace(
                0,
                np.nan
            )
        )

        # ----------------------------------------------------------
        # Candle body
        # ----------------------------------------------------------

        candle_range = (
            df["High"]
            -
            df["Low"]
        )

        df["Candle_Range"] = (
            candle_range
        )

        df["Candle_Body"] = (
            df["Close"]
            -
            df["Open"]
        ).abs()

        df["Body_Ratio"] = (
            df["Candle_Body"]
            /
            candle_range.replace(
                0,
                np.nan
            )
        )

        # ----------------------------------------------------------
        # Bullish / bearish candle
        # ----------------------------------------------------------

        df["Bullish_Candle"] = (
            df["Close"]
            >
            df["Open"]
        )

        df["Bearish_Candle"] = (
            df["Close"]
            <
            df["Open"]
        )

        # ----------------------------------------------------------
        # Momentum
        # ----------------------------------------------------------

        df["ROC_5"] = (
            df["Close"]
            .pct_change(5)
            * 100.0
        )

        # ----------------------------------------------------------
        # Data validity
        # ----------------------------------------------------------

        required_columns = [
            "EMA_50",
            "EMA_200",
            "ATR_14",
            "ATR_Pct",
            "EMA_Separation_ATR",
            "EMA50_Slope_ATR",
            "Relative_Volume",
            "Body_Ratio",
            "ROC_5"
        ]

        df.replace(
            [np.inf, -np.inf],
            np.nan,
            inplace=True
        )

        return df

    # ==================================================================
    # PREPARE TIMEFRAME
    # ==================================================================

    def prepare_timeframe(
        self,
        timeframe: str
    ):

        if timeframe not in self.timeframes_data:

            return False

        df = self.timeframes_data[
            timeframe
        ]

        df = self.calculate_indicators(
            df
        )

        self.timeframes_data[
            timeframe
        ] = df

        return True

    # ==================================================================
    # GET CLOSED CANDLE
    # ==================================================================

    @staticmethod
    def closed_candle(
        df: pd.DataFrame
    ):

        if len(df) < 3:

            raise ValueError(
                "Not enough candles."
            )

        # -1 = potentially still forming
        # -2 = last fully closed candle

        return df.iloc[-2]

    # ==================================================================
    # TREND ENGINE
    # ==================================================================

    def get_trend_state(
        self,
        df: pd.DataFrame
    ):

        candle = self.closed_candle(
            df
        )

        ema50 = float(
            candle["EMA_50"]
        )

        ema200 = float(
            candle["EMA_200"]
        )

        slope50 = float(
            candle["EMA50_Slope_ATR"]
        )

        slope200 = float(
            candle["EMA200_Slope_ATR"]
        )

        separation = float(
            candle["EMA_Separation_ATR"]
        )

        close = float(
            candle["Close"]
        )

        # ----------------------------------------------------------
        # Validate
        # ----------------------------------------------------------

        values = [
            ema50,
            ema200,
            slope50,
            slope200,
            separation,
            close
        ]

        if not all(
            self.is_valid_number(v)
            for v in values
        ):

            return {
                "trend": "INVALID"
            }

        # ----------------------------------------------------------
        # Bullish
        # ----------------------------------------------------------

        if (
            ema50 > ema200
            and
            slope50 > 0
            and
            slope200 >= 0
        ):

            trend = "BULLISH"

        # ----------------------------------------------------------
        # Bearish
        # ----------------------------------------------------------

        elif (
            ema50 < ema200
            and
            slope50 > 0
            and
            slope200 >= 0
        ):

            # This branch is intentionally NOT used.
            # It prevents incorrectly treating positive
            # absolute slopes as bearish direction.
            trend = "BEARISH"

        else:

            # Determine bearish trend correctly.
            if (
                ema50 < ema200
                and
                slope50 >= 0
            ):
                trend = "BEARISH"

            elif (
                ema50 < ema200
                and
                slope50 > 0
            ):
                trend = "BEARISH"

            elif (
                ema50 > ema200
                and
                slope50 > 0
            ):
                trend = "BULLISH"

            else:
                trend = "NEUTRAL"

        # ----------------------------------------------------------
        # Correct directional slope
        # ----------------------------------------------------------

        if (
            ema50 > ema200
            and
            (
                candle["EMA50_Slope"]
                if "EMA50_Slope" in candle
                else 0
            ) > 0
        ):

            trend = "BULLISH"

        elif (
            ema50 < ema200
            and
            (
                candle["EMA50_Slope"]
                if "EMA50_Slope" in candle
                else 0
            ) < 0
        ):

            trend = "BEARISH"

        else:

            trend = "NEUTRAL"

        # ----------------------------------------------------------
        # Trend strength
        # ----------------------------------------------------------

        strength = min(
            separation / 2.0,
            1.0
        )

        return {

            "trend": trend,

            "ema50": ema50,

            "ema200": ema200,

            "close": close,

            "separation_atr":
                separation,

            "slope_atr":
                slope50,

            "strength":
                round(
                    strength * 100.0,
                    2
                )
        }

    # ==================================================================
    # CROSSOVER ENGINE
    # ==================================================================

    @staticmethod
    def detect_crossover(
        df: pd.DataFrame
    ):

        if len(df) < 4:

            return "NEUTRAL"

        # ----------------------------------------------------------
        # Closed candles only
        # ----------------------------------------------------------

        current = df.iloc[-2]
        previous = df.iloc[-3]

        curr50 = float(
            current["EMA_50"]
        )

        curr200 = float(
            current["EMA_200"]
        )

        prev50 = float(
            previous["EMA_50"]
        )

        prev200 = float(
            previous["EMA_200"]
        )

        # ----------------------------------------------------------
        # Bullish cross
        # ----------------------------------------------------------

        bullish = (
            prev50 <= prev200
            and
            curr50 > curr200
        )

        # ----------------------------------------------------------
        # Bearish cross
        # ----------------------------------------------------------

        bearish = (
            prev50 >= prev200
            and
            curr50 < curr200
        )

        if bullish:

            return "BUY"

        if bearish:

            return "SELL"

        return "NEUTRAL"

    # ==================================================================
    # MARKET REGIME
    # ==================================================================

    def detect_market_regime(
        self,
        df: pd.DataFrame
    ):

        candle = self.closed_candle(
            df
        )

        atr_pct = float(
            candle["ATR_Pct"]
        )

        separation = float(
            candle["EMA_Separation_ATR"]
        )

        relative_volume = float(
            candle["Relative_Volume"]
        )

        if not all(
            self.is_valid_number(v)
            for v in [
                atr_pct,
                separation,
                relative_volume
            ]
        ):

            return "INVALID"

        # ----------------------------------------------------------
        # Extreme volatility
        # ----------------------------------------------------------

        if atr_pct > self.max_atr_pct:

            return "EXTREME_VOLATILITY"

        # ----------------------------------------------------------
        # Very weak EMA separation
        # ----------------------------------------------------------

        if separation < 0.20:

            return "RANGE"

        # ----------------------------------------------------------
        # Strong trend
        # ----------------------------------------------------------

        if (
            separation >= 1.0
            and
            relative_volume >= 0.80
        ):

            return "TRENDING"

        # ----------------------------------------------------------
        # Normal market
        # ----------------------------------------------------------

        return "NORMAL"

    # ==================================================================
    # CANDLE QUALITY
    # ==================================================================

    @staticmethod
    def candle_quality(
        df: pd.DataFrame,
        direction: str
    ):

        candle = df.iloc[-2]

        body_ratio = float(
            candle["Body_Ratio"]
        )

        bullish = bool(
            candle["Bullish_Candle"]
        )

        bearish = bool(
            candle["Bearish_Candle"]
        )

        # ----------------------------------------------------------
        # Directional candle
        # ----------------------------------------------------------

        if direction == "BUY":

            if bullish and body_ratio >= 0.55:

                return 1.0

            if bullish and body_ratio >= 0.35:

                return 0.5

        elif direction == "SELL":

            if bearish and body_ratio >= 0.55:

                return 1.0

            if bearish and body_ratio >= 0.35:

                return 0.5

        return 0.0

    # ==================================================================
    # SIGNAL SCORE
    # ==================================================================

    def calculate_signal_score(
        self,
        direction: str,
        trend_1d: dict,
        trend_4h: dict,
        df_15m: pd.DataFrame
    ):

        score = 0.0

        candle = self.closed_candle(
            df_15m
        )

        # ----------------------------------------------------------
        # 1D alignment
        # ----------------------------------------------------------

        if (
            direction == "BUY"
            and
            trend_1d["trend"] == "BULLISH"
        ):

            score += 25.0

        elif (
            direction == "SELL"
            and
            trend_1d["trend"] == "BEARISH"
        ):

            score += 25.0

        # ----------------------------------------------------------
        # 4H alignment
        # ----------------------------------------------------------

        if (
            direction == "BUY"
            and
            trend_4h["trend"] == "BULLISH"
        ):

            score += 25.0

        elif (
            direction == "SELL"
            and
            trend_4h["trend"] == "BEARISH"
        ):

            score += 25.0

        # ----------------------------------------------------------
        # 15M EMA alignment
        # ----------------------------------------------------------

        ema50 = float(
            candle["EMA_50"]
        )

        ema200 = float(
            candle["EMA_200"]
        )

        if (
            direction == "BUY"
            and
            ema50 > ema200
        ):

            score += 10.0

        elif (
            direction == "SELL"
            and
            ema50 < ema200
        ):

            score += 10.0

        # ----------------------------------------------------------
        # EMA separation
        # ----------------------------------------------------------

        separation = float(
            candle["EMA_Separation_ATR"]
        )

        if separation >= 0.50:

            score += 5.0

        if separation >= 1.00:

            score += 5.0

        # ----------------------------------------------------------
        # Slope
        # ----------------------------------------------------------

        raw_slope = float(
            candle["EMA50_Slope"]
        )

        atr = float(
            candle["ATR_14"]
        )

        normalized_slope = (
            raw_slope / atr
            if atr > 0
            else 0
        )

        if (
            direction == "BUY"
            and
            normalized_slope > 0.05
        ):

            score += 5.0

        elif (
            direction == "SELL"
            and
            normalized_slope < -0.05
        ):

            score += 5.0

        # ----------------------------------------------------------
        # Relative volume
        # ----------------------------------------------------------

        relative_volume = float(
            candle["Relative_Volume"]
        )

        if relative_volume >= 1.0:

            score += 5.0

        elif (
            relative_volume
            >= self.min_relative_volume
        ):

            score += 2.5

        # ----------------------------------------------------------
        # Candle quality
        # ----------------------------------------------------------

        quality = self.candle_quality(
            df_15m,
            direction
        )

        score += (
            quality * 5.0
        )

        # ----------------------------------------------------------
        # Momentum
        # ----------------------------------------------------------

        roc = float(
            candle["ROC_5"]
        )

        if direction == "BUY" and roc > 0:

            score += 5.0

        elif direction == "SELL" and roc < 0:

            score += 5.0

        # ----------------------------------------------------------
        # Maximum
        # ----------------------------------------------------------

        return round(
            min(score, 100.0),
            2
        )

    # ==================================================================
    # STOP LOSS ENGINE
    # ==================================================================

    def calculate_stop_loss(
        self,
        df: pd.DataFrame,
        direction: str
    ):

        if len(df) < (
            self.structure_lookback + 5
        ):

            raise ValueError(
                "Insufficient candles for SL."
            )

        candle = self.closed_candle(
            df
        )

        entry = float(
            candle["Close"]
        )

        ema200 = float(
            candle["EMA_200"]
        )

        atr = float(
            candle["ATR_14"]
        )

        if not all(
            self.is_valid_number(v)
            for v in [
                entry,
                ema200,
                atr
            ]
        ):

            raise ValueError(
                "Invalid SL inputs."
            )

        if atr <= 0:

            raise ValueError(
                "ATR must be positive."
            )

        # ----------------------------------------------------------
        # CLOSED candles only
        # Exclude current forming candle.
        # ----------------------------------------------------------

        structure = df.iloc[
            -(self.structure_lookback + 2):-2
        ]

        recent_low = float(
            structure["Low"].min()
        )

        recent_high = float(
            structure["High"].max()
        )

        buffer = (
            atr
            *
            self.atr_stop_buffer
        )

        # ----------------------------------------------------------
        # BUY
        # ----------------------------------------------------------

        if direction == "BUY":

            structural_sl = (
                recent_low
                -
                buffer
            )

            ema_sl = (
                ema200
                -
                buffer
            )

            stop_loss = min(
                structural_sl,
                ema_sl
            )

            # ------------------------------------------------------
            # Ensure SL below entry
            # ------------------------------------------------------

            if stop_loss >= entry:

                stop_loss = (
                    entry
                    -
                    atr
                )

        # ----------------------------------------------------------
        # SELL
        # ----------------------------------------------------------

        elif direction == "SELL":

            structural_sl = (
                recent_high
                +
                buffer
            )

            ema_sl = (
                ema200
                +
                buffer
            )

            stop_loss = max(
                structural_sl,
                ema_sl
            )

            # ------------------------------------------------------
            # Ensure SL above entry
            # ------------------------------------------------------

            if stop_loss <= entry:

                stop_loss = (
                    entry
                    +
                    atr
                )

        else:

            raise ValueError(
                "Invalid direction."
            )

        # ----------------------------------------------------------
        # Validate stop distance
        # ----------------------------------------------------------

        stop_distance = abs(
            entry - stop_loss
        )

        min_distance = (
            atr
            *
            self.min_stop_atr
        )

        max_distance = (
            atr
            *
            self.max_stop_atr
        )

        # ----------------------------------------------------------
        # Too tight
        # ----------------------------------------------------------

        if stop_distance < min_distance:

            if direction == "BUY":

                stop_loss = (
                    entry
                    -
                    min_distance
                )

            else:

                stop_loss = (
                    entry
                    +
                    min_distance
                )

        # ----------------------------------------------------------
        # Too wide
        #
        # Reject instead of silently forcing
        # a dangerous SL.
        # ----------------------------------------------------------

        stop_distance = abs(
            entry - stop_loss
        )

        if stop_distance > max_distance:

            raise ValueError(
                "Stop distance exceeds "
                "maximum allowed ATR distance."
            )

        return float(
            stop_loss
        )

    # ==================================================================
    # RISK ENGINE
    # ==================================================================

    def calculate_risk_management(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str
    ):

        entry_price = float(
            entry_price
        )

        stop_loss = float(
            stop_loss
        )

        # ----------------------------------------------------------
        # Validate
        # ----------------------------------------------------------

        if not all(
            self.is_valid_number(v)
            for v in [
                entry_price,
                stop_loss
            ]
        ):

            raise ValueError(
                "Invalid price."
            )

        # ----------------------------------------------------------
        # Risk capital
        # ----------------------------------------------------------

        risk_amount = (
            self.balance
            *
            self.risk_pct
            /
            100.0
        )

        if risk_amount <= 0:

            raise ValueError(
                "Risk amount must be positive."
            )

        # ----------------------------------------------------------
        # BUY
        # ----------------------------------------------------------

        if direction == "BUY":

            if stop_loss >= entry_price:

                raise ValueError(
                    "BUY SL must be below entry."
                )

            price_risk = (
                entry_price
                -
                stop_loss
            )

            take_profit = (
                entry_price
                +
                price_risk
                *
                self.reward_risk
            )

        # ----------------------------------------------------------
        # SELL
        # ----------------------------------------------------------

        elif direction == "SELL":

            if stop_loss <= entry_price:

                raise ValueError(
                    "SELL SL must be above entry."
                )

            price_risk = (
                stop_loss
                -
                entry_price
            )

            take_profit = (
                entry_price
                -
                price_risk
                *
                self.reward_risk
            )

        else:

            raise ValueError(
                "Invalid direction."
            )

        if price_risk <= 0:

            raise ValueError(
                "Price risk must be positive."
            )

        # ----------------------------------------------------------
        # Position size
        #
        # For linear USDT contracts:
        #
        # Position size = Risk / price distance
        #
        # This is a planning quantity, not an exchange
        # order quantity until contract specifications are
        # validated.
        # ----------------------------------------------------------

        position_size = (
            risk_amount
            /
            price_risk
        )

        notional = (
            position_size
            *
            entry_price
        )

        stop_distance_pct = (
            price_risk
            /
            entry_price
        ) * 100.0

        # ----------------------------------------------------------
        # Leverage-independent risk
        # ----------------------------------------------------------

        return {

            "Risk_Amount_USD":
                round(
                    risk_amount,
                    4
                ),

            "Entry_Price":
                round(
                    entry_price,
                    8
                ),

            "Stop_Loss":
                round(
                    stop_loss,
                    8
                ),

            "Take_Profit":
                round(
                    take_profit,
                    8
                ),

            "Position_Size":
                round(
                    position_size,
                    8
                ),

            "Notional_Value":
                round(
                    notional,
                    4
                ),

            "Stop_Distance_Pct":
                round(
                    stop_distance_pct,
                    4
                ),

            "Risk_Reward_Ratio":
                f"1:{self.reward_risk:.2f}"
        }

    # ==================================================================
    # FINAL SIGNAL VALIDATION
    # ==================================================================

    def validate_signal(
        self,
        result: dict
    ):

        signal = result.get(
            "signal"
        )

        if signal not in (
            "BUY",
            "SELL"
        ):

            return False, (
                "Invalid signal."
            )

        score = float(
            result.get(
                "score",
                0
            )
        )

        if score < self.min_score:

            return False, (
                "Score below minimum."
            )

        # ----------------------------------------------------------
        # Direction alignment
        # ----------------------------------------------------------

        if signal == "BUY":

            if result["trend_1d"] != "BULLISH":

                return False, (
                    "1D trend mismatch."
                )

            if result["trend_4h"] != "BULLISH":

                return False, (
                    "4H trend mismatch."
                )

        else:

            if result["trend_1d"] != "BEARISH":

                return False, (
                    "1D trend mismatch."
                )

            if result["trend_4h"] != "BEARISH":

                return False, (
                    "4H trend mismatch."
                )

        # ----------------------------------------------------------
        # Volatility
        # ----------------------------------------------------------

        if result["volatility"] == (
            "EXTREME_VOLATILITY"
        ):

            return False, (
                "Extreme volatility."
            )

        # ----------------------------------------------------------
        # Relative volume
        # ----------------------------------------------------------

        if (
            result["relative_volume"]
            <
            self.min_relative_volume
        ):

            return False, (
                "Insufficient relative volume."
            )

        # ----------------------------------------------------------
        # Risk plan
        # ----------------------------------------------------------

        trade = result.get(
            "trade_plan"
        )

        if not trade:

            return False, (
                "Missing trade plan."
            )

        if (
            trade["Risk_Amount_USD"]
            <= 0
        ):

            return False, (
                "Invalid risk."
            )

        if (
            trade["Position_Size"]
            <= 0
        ):

            return False, (
                "Invalid position size."
            )

        return True, "VALID"

    # ==================================================================
    # COMPLETE STRATEGY
    # ==================================================================

    def check_strategy(self):

        required = [
            "1d",
            "4h",
            "15m"
        ]

        # ----------------------------------------------------------
        # Verify data
        # ----------------------------------------------------------

        for tf in required:

            if tf not in self.timeframes_data:

                return {
                    "signal": "NEUTRAL",
                    "reason":
                        f"Missing {tf} data."
                }

        # ----------------------------------------------------------
        # Prepare
        # ----------------------------------------------------------

        for tf in required:

            if not self.prepare_timeframe(
                tf
            ):

                return {
                    "signal": "NEUTRAL",
                    "reason":
                        f"Failed to prepare {tf}."
                }

        df_1d = self.timeframes_data[
            "1d"
        ]

        df_4h = self.timeframes_data[
            "4h"
        ]

        df_15m = self.timeframes_data[
            "15m"
        ]

        # ----------------------------------------------------------
        # Trend
        # ----------------------------------------------------------

        trend_1d = (
            self.get_trend_state(
                df_1d
            )
        )

        trend_4h = (
            self.get_trend_state(
                df_4h
            )
        )

        if (
            trend_1d["trend"]
            == "INVALID"
            or
            trend_4h["trend"]
            == "INVALID"
        ):

            return {
                "signal": "NEUTRAL",
                "reason":
                    "Invalid higher timeframe data."
            }

        # ----------------------------------------------------------
        # 15M crossover
        # ----------------------------------------------------------

        crossover = (
            self.detect_crossover(
                df_15m
            )
        )

        if crossover == "NEUTRAL":

            return {

                "signal":
                    "NEUTRAL",

                "reason":
                    "No confirmed 15M EMA crossover.",

                "trend_1d":
                    trend_1d["trend"],

                "trend_4h":
                    trend_4h["trend"]
            }

        # ----------------------------------------------------------
        # HTF alignment
        # ----------------------------------------------------------

        if crossover == "BUY":

            aligned = (
                trend_1d["trend"]
                ==
                "BULLISH"
                and
                trend_4h["trend"]
                ==
                "BULLISH"
            )

        else:

            aligned = (
                trend_1d["trend"]
                ==
                "BEARISH"
                and
                trend_4h["trend"]
                ==
                "BEARISH"
            )

        if not aligned:

            return {

                "signal":
                    "NEUTRAL",

                "reason":
                    "Higher timeframe misalignment.",

                "trend_1d":
                    trend_1d["trend"],

                "trend_4h":
                    trend_4h["trend"],

                "crossover":
                    crossover
            }

        # ----------------------------------------------------------
        # Market regime
        # ----------------------------------------------------------

        regime = (
            self.detect_market_regime(
                df_15m
            )
        )

        if regime in (
            "INVALID",
            "RANGE",
            "EXTREME_VOLATILITY"
        ):

            return {

                "signal":
                    "NEUTRAL",

                "reason":
                    f"Market regime rejected: {regime}",

                "trend_1d":
                    trend_1d["trend"],

                "trend_4h":
                    trend_4h["trend"],

                "crossover":
                    crossover,

                "regime":
                    regime
            }

        # ----------------------------------------------------------
        # Score
        # ----------------------------------------------------------

        score = (
            self.calculate_signal_score(
                crossover,
                trend_1d,
                trend_4h,
                df_15m
            )
        )

        # ----------------------------------------------------------
        # Entry
        # ----------------------------------------------------------

        signal_candle = (
            self.closed_candle(
                df_15m
            )
        )

        entry_price = float(
            signal_candle["Close"]
        )

        # ----------------------------------------------------------
        # Stop Loss
        # ----------------------------------------------------------

        try:

            stop_loss = (
                self.calculate_stop_loss(
                    df_15m,
                    crossover
                )
            )

        except Exception as exc:

            return {

                "signal":
                    "NEUTRAL",

                "reason":
                    f"SL rejected: {exc}",

                "trend_1d":
                    trend_1d["trend"],

                "trend_4h":
                    trend_4h["trend"],

                "crossover":
                    crossover,

                "score":
                    score
            }

        # ----------------------------------------------------------
        # Risk
        # ----------------------------------------------------------

        try:

            trade_plan = (
                self.calculate_risk_management(
                    entry_price,
                    stop_loss,
                    crossover
                )
            )

        except Exception as exc:

            return {

                "signal":
                    "NEUTRAL",

                "reason":
                    f"Risk rejected: {exc}",

                "trend_1d":
                    trend_1d["trend"],

                "trend_4h":
                    trend_4h["trend"],

                "crossover":
                    crossover,

                "score":
                    score
            }

        # ----------------------------------------------------------
        # Timestamp
        # ----------------------------------------------------------

        signal_timestamp = (
            signal_candle["Timestamp"]
        )

        # ----------------------------------------------------------
        # Unique signal
        # ----------------------------------------------------------

        signal_id = (
            f"{self.symbol}|"
            f"{crossover}|"
            f"{signal_timestamp.isoformat()}"
        )

        # ----------------------------------------------------------
        # Build result
        # ----------------------------------------------------------

        result = {

            "signal":
                crossover,

            "score":
                score,

            "signal_id":
                signal_id,

            "signal_timestamp":
                signal_timestamp,

            "trend_1d":
                trend_1d["trend"],

            "trend_4h":
                trend_4h["trend"],

            "trend_strength_1d":
                trend_1d["strength"],

            "trend_strength_4h":
                trend_4h["strength"],

            "ema50_1d":
                trend_1d["ema50"],

            "ema200_1d":
                trend_1d["ema200"],

            "ema50_4h":
                trend_4h["ema50"],

            "ema200_4h":
                trend_4h["ema200"],

            "ema50_15m":
                float(
                    signal_candle[
                        "EMA_50"
                    ]
                ),

            "ema200_15m":
                float(
                    signal_candle[
                        "EMA_200"
                    ]
                ),

            "ema_separation_atr":
                float(
                    signal_candle[
                        "EMA_Separation_ATR"
                    ]
                ),

            "ema_slope_atr":
                float(
                    signal_candle[
                        "EMA50_Slope_ATR"
                    ]
                ),

            "atr_15m":
                float(
                    signal_candle[
                        "ATR_14"
                    ]
                ),

            "atr_pct":
                float(
                    signal_candle[
                        "ATR_Pct"
                    ]
                ),

            "relative_volume":
                float(
                    signal_candle[
                        "Relative_Volume"
                    ]
                ),

            "roc_5":
                float(
                    signal_candle[
                        "ROC_5"
                    ]
                ),

            "body_ratio":
                float(
                    signal_candle[
                        "Body_Ratio"
                    ]
                ),

            "volatility":
                regime,

            "trade_plan":
                trade_plan
        }

        # ----------------------------------------------------------
        # Final validation
        # ----------------------------------------------------------

        valid, reason = (
            self.validate_signal(
                result
            )
        )

        result[
            "validated"
        ] = valid

        result[
            "validation_reason"
        ] = reason

        if not valid:

            result[
                "signal"
            ] = "NEUTRAL"

            result[
                "reason"
            ] = reason

        return result

    # ==================================================================
    # TELEGRAM
    # ==================================================================

    def send_telegram_alert(
        self,
        result: dict
    ):

        if not self.telegram_token:

            return False

        if not self.chat_id:

            return False

        trade = result[
            "trade_plan"
        ]

        message = (
            "🚨 EXCORA QUANT SIGNAL 🚨\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Symbol: {self.symbol}\n"
            f"Direction: {result['signal']}\n"
            f"Score: {result['score']}/100\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Entry: {trade['Entry_Price']}\n"
            f"SL: {trade['Stop_Loss']}\n"
            f"TP: {trade['Take_Profit']}\n"
            f"RR: {trade['Risk_Reward_Ratio']}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Risk: ${trade['Risk_Amount_USD']}\n"
            f"Position Size: {trade['Position_Size']}\n"
            f"Notional: ${trade['Notional_Value']}\n"
            f"Stop Distance: {trade['Stop_Distance_Pct']}%\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"1D Trend: {result['trend_1d']}\n"
            f"4H Trend: {result['trend_4h']}\n"
            f"15M EMA50: {result['ema50_15m']:.8f}\n"
            f"15M EMA200: {result['ema200_15m']:.8f}\n"
            f"EMA Separation: "
            f"{result['ema_separation_atr']:.3f} ATR\n"
            f"EMA Slope: "
            f"{result['ema_slope_atr']:.3f} ATR\n"
            f"ATR: {result['atr_15m']:.8f}\n"
            f"ATR %: {result['atr_pct']:.3f}%\n"
            f"Relative Volume: "
            f"{result['relative_volume']:.2f}\n"
            f"Momentum ROC: "
            f"{result['roc_5']:.3f}%\n"
            f"Candle Quality: "
            f"{result['body_ratio']:.2f}\n"
            f"Regime: {result['volatility']}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "1D → 4H → 15M\n"
            "EMA50/200 + ATR + Volume + "
            "Momentum + Risk Engine\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ SIGNAL ONLY — NO AUTO EXECUTION"
        )

        url = (
            "https://api.telegram.org/"
            f"bot{self.telegram_token}/sendMessage"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": message
        }

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=10
            )

            response.raise_for_status()

            return True

        except Exception as exc:

            logger.error(
                f"Telegram error | "
                f"{self.symbol} | "
                f"{exc}"
            )

            return False

    # ==================================================================
    # SCAN
    # ==================================================================

    def scan(self):

        self.last_scan_time = (
            datetime.now(
                timezone.utc
            )
        )

        # ----------------------------------------------------------
        # Fetch all timeframes
        # ----------------------------------------------------------

        if not self.fetch_live_data(
            "1d",
            350
        ):

            return None

        if not self.fetch_live_data(
            "4h",
            350
        ):

            return None

        if not self.fetch_live_data(
            "15m",
            350
        ):

            return None

        # ----------------------------------------------------------
        # Strategy
        # ----------------------------------------------------------

        return self.check_strategy()


# ==================================================================
# EXCORA RUNNER
# ==================================================================

if __name__ == "__main__":

    # ==============================================================
    # SYMBOLS
    # ==============================================================

    LIVE_SYMBOLS = [

        "BTC/USDT:USDT",

        "ETH/USDT:USDT",

        "SOL/USDT:USDT",

        "XRP/USDT:USDT"
    ]

    # ==============================================================
    # ACCOUNT
    # ==============================================================

    ACCOUNT_BALANCE = 100.0

    RISK_PERCENT = 1.0

    REWARD_RISK = 3.0

    # ==============================================================
    # SIGNAL FILTER
    # ==============================================================

    MIN_SCORE = 75.0

    # ==============================================================
    # SCAN INTERVAL
    # ==============================================================

    SCAN_INTERVAL = 120

    # ==============================================================
    # TELEGRAM
    # ==============================================================

    TELEGRAM_TOKEN = (
        "8716831426:AAF9AwmGPvWw_ucFCSH7dqEhwd8VCskY4Q4"
    )

    CHAT_ID = (
        "8297464896"
    )

    # ==============================================================
    # HEADER
    # ==============================================================

    print("=" * 90)

    print(
        "🏛 EXCORA QUANT EMA MASTER"
    )

    print(
        "1D → 4H → 15M"
    )

    print(
        "EMA50/200 + Slope + "
        "EMA Separation + ATR + "
        "Volume + Momentum + "
        "Regime + Risk Engine"
    )

    print(
        "SIGNAL ONLY — NO AUTO EXECUTION"
    )

    print("=" * 90)

    # ==============================================================
    # CREATE ENGINES
    # ==============================================================

    engines = {}

    for symbol in LIVE_SYMBOLS:

        engines[symbol] = (
            ExcoraTripleTFQuantEngine(

                symbol=symbol,

                balance=ACCOUNT_BALANCE,

                risk_per_trade_pct=
                    RISK_PERCENT,

                reward_risk=
                    REWARD_RISK,

                telegram_token=
                    TELEGRAM_TOKEN,

                chat_id=
                    CHAT_ID,

                min_score=
                    MIN_SCORE
            )
        )

    # ==============================================================
    # MAIN LOOP
    # ==============================================================

    while True:

        scan_time = (
            datetime.now(
                timezone.utc
            )
            .strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )

        print()
        print("=" * 90)

        print(
            f"🔄 EXCORA MARKET SCAN | "
            f"{scan_time}"
        )

        print("=" * 90)

        # ----------------------------------------------------------
        # Each asset
        # ----------------------------------------------------------

        for symbol in LIVE_SYMBOLS:

            engine = engines[
                symbol
            ]

            try:

                result = engine.scan()

                if not result:

                    print(
                        f"❌ [{symbol}] "
                        "DATA UNAVAILABLE"
                    )

                    continue

                signal = result.get(
                    "signal",
                    "NEUTRAL"
                )

                # ==================================================
                # NEUTRAL
                # ==================================================

                if signal == "NEUTRAL":

                    reason = result.get(
                        "reason",
                        "No valid signal."
                    )

                    print(
                        f"⚪ [{symbol}] "
                        f"NEUTRAL | "
                        f"{reason}"
                    )

                    continue

                # ==================================================
                # SCORE
                # ==================================================

                score = float(
                    result.get(
                        "score",
                        0
                    )
                )

                # ==================================================
                # MINIMUM SCORE
                # ==================================================

                if score < MIN_SCORE:

                    print(
                        f"🟡 [{symbol}] "
                        f"{signal} REJECTED | "
                        f"Score={score:.2f} | "
                        f"Minimum={MIN_SCORE:.2f}"
                    )

                    continue

                # ==================================================
                # VALIDATION
                # ==================================================

                if not result.get(
                    "validated",
                    False
                ):

                    print(
                        f"🟠 [{symbol}] "
                        f"SIGNAL FAILED VALIDATION | "
                        f"{result.get('validation_reason')}"
                    )

                    continue

                # ==================================================
                # TRADE PLAN
                # ==================================================

                trade = result[
                    "trade_plan"
                ]

                # ==================================================
                # OUTPUT
                # ==================================================

                print()
                print(
                    f"🔥 [{symbol}] "
                    f"{signal} | "
                    f"Score={score:.2f}/100"
                )

                print(
                    f"   1D Trend: "
                    f"{result['trend_1d']}"
                )

                print(
                    f"   4H Trend: "
                    f"{result['trend_4h']}"
                )

                print(
                    f"   Regime: "
                    f"{result['volatility']}"
                )

                print(
                    f"   Entry: "
                    f"{trade['Entry_Price']}"
                )

                print(
                    f"   Stop Loss: "
                    f"{trade['Stop_Loss']}"
                )

                print(
                    f"   Take Profit: "
                    f"{trade['Take_Profit']}"
                )

                print(
                    f"   RR: "
                    f"{trade['Risk_Reward_Ratio']}"
                )

                print(
                    f"   Risk: "
                    f"${trade['Risk_Amount_USD']}"
                )

                print(
                    f"   Position Size: "
                    f"{trade['Position_Size']}"
                )

                print(
                    f"   Notional: "
                    f"${trade['Notional_Value']}"
                )

                print(
                    f"   Stop Distance: "
                    f"{trade['Stop_Distance_Pct']}%"
                )

                print(
                    f"   EMA Separation: "
                    f"{result['ema_separation_atr']:.3f} ATR"
                )

                print(
                    f"   EMA Slope: "
                    f"{result['ema_slope_atr']:.3f} ATR"
                )

                print(
                    f"   Relative Volume: "
                    f"{result['relative_volume']:.2f}"
                )

                print(
                    f"   Momentum ROC: "
                    f"{result['roc_5']:.3f}%"
                )

                # ==================================================
                # SIGNAL ID
                # ==================================================

                signal_id = result[
                    "signal_id"
                ]

                # ==================================================
                # DUPLICATE PROTECTION
                # ==================================================

                if (
                    engine.last_signal_id
                    != signal_id
                ):

                    print(
                        "   🚀 NEW CONFIRMED "
                        "EXCORA SIGNAL"
                    )

                    # ------------------------------------------------
                    # Telegram
                    #
                    # Enable only after Paper Trading validation.
                    # ------------------------------------------------

                    # engine.send_telegram_alert(
                    #     result
                    # )

                    engine.last_signal_id = (
                        signal_id
                    )

                else:

                    print(
                        "   ⏸ DUPLICATE "
                        "SIGNAL IGNORED"
                    )

            except Exception as exc:

                logger.exception(
                    f"ENGINE ERROR | "
                    f"{symbol} | "
                    f"{exc}"
                )

        # ==========================================================
        # WAIT
        # ==========================================================

        print()

        print(
            f"⏳ Next scan in "
            f"{SCAN_INTERVAL} seconds..."
        )

        print("=" * 90)

        time.sleep(
            SCAN_INTERVAL
        )
