from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from api.services.binance_data import BinanceDataService
from core.data.models import OHLCV
from core.pipeline.quant_pipeline import QuantPipeline


class QuantService:
    """
    CAPITAL WISE
    =========================

    Quantitative analysis service.

    Data flow:

        Request
           ↓
        BinanceDataService
           ↓
        OHLCV + Volume
           ↓
        QuantPipeline
           ↓
        Profile
        Dynamics
        Market State
        Probability
        Expected Value
        Signal
        Risk
           ↓
        API Response

    Binance is used directly through REST.
    No CCXT dependency.
    """

    def __init__(
        self,
        risk_percent: float = 0.01,
        reward_risk: float = 3.0,
        value_area: float = 0.70,
    ) -> None:

        self.pipeline = QuantPipeline(
            risk_percent=risk_percent,
            reward_risk=reward_risk,
            value_area=value_area,
        )

        self.market_data = BinanceDataService()

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    @staticmethod
    def _serialize(value: Any) -> Any:
        """
        Convert dataclasses, NumPy objects,
        dictionaries and sequences into JSON-safe values.
        """

        if value is None:
            return None

        # Dataclass
        if hasattr(value, "__dataclass_fields__"):
            return QuantService._serialize(
                asdict(value)
            )

        # NumPy
        if isinstance(value, np.ndarray):
            return [
                QuantService._serialize(item)
                for item in value.tolist()
            ]

        if isinstance(value, np.integer):
            return int(value)

        if isinstance(value, np.floating):
            return float(value)

        if isinstance(value, np.bool_):
            return bool(value)

        # Dictionary
        if isinstance(value, dict):
            return {
                str(key): QuantService._serialize(item)
                for key, item in value.items()
            }

        # List / Tuple
        if isinstance(value, (list, tuple)):
            return [
                QuantService._serialize(item)
                for item in value
            ]

        # Primitive
        return value

    # ==========================================================
    # MARKET DATA
    # ==========================================================

    def _load_candles(self, request) -> tuple[list[OHLCV], str]:
        """
        Load candles from request or Binance.

        Priority:

        1. Request candles, if supplied.
        2. Binance live market data.
        """

        # ------------------------------------------------------
        # REQUEST DATA
        # ------------------------------------------------------

        if request.candles:

            candles = [
                OHLCV(
                    timestamp=c.timestamp,
                    open=float(c.open),
                    high=float(c.high),
                    low=float(c.low),
                    close=float(c.close),
                    volume=float(c.volume),
                    symbol=c.symbol,
                    market=c.market,
                    timeframe=c.timeframe,
                )
                for c in request.candles
            ]

            return candles, "REQUEST"

        # ------------------------------------------------------
        # BINANCE LIVE DATA
        # ------------------------------------------------------

        candles = self.market_data.fetch_ohlcv(
            symbol=request.symbol,
            timeframe=request.timeframe,
            limit=request.limit,
            market=request.market,
        )

        return candles, "BINANCE"

    # ==========================================================
    # VALIDATION
    # ==========================================================

    @staticmethod
    def _validate_candles(
        candles: list[OHLCV],
    ) -> None:

        if len(candles) < 2:
            raise ValueError(
                "Not enough candles for quantitative analysis"
            )

        volume_sum = sum(
            float(candle.volume)
            for candle in candles
        )

        if volume_sum <= 0:
            raise ValueError(
                "Market data contains zero volume"
            )

        for candle in candles:

            if candle.high < candle.low:
                raise ValueError(
                    "Invalid candle: high is below low"
                )

            if candle.open <= 0:
                raise ValueError(
                    "Invalid candle: open price must be positive"
                )

            if candle.close <= 0:
                raise ValueError(
                    "Invalid candle: close price must be positive"
                )

            if candle.volume < 0:
                raise ValueError(
                    "Invalid candle: volume cannot be negative"
                )

    # ==========================================================
    # ANALYSIS
    # ==========================================================

    def analyze(self, request) -> dict[str, Any]:
        """
        Execute complete quantitative analysis.
        """

        # ------------------------------------------------------
        # 1. MARKET DATA
        # ------------------------------------------------------

        candles, data_source = self._load_candles(
            request
        )

        # ------------------------------------------------------
        # 2. DATA VALIDATION
        # ------------------------------------------------------

        self._validate_candles(
            candles
        )

        # ------------------------------------------------------
        # 3. VOLUME
        # ------------------------------------------------------

        volume_sum = sum(
            float(candle.volume)
            for candle in candles
        )

        # ------------------------------------------------------
        # 4. LIVE ENTRY
        # ------------------------------------------------------

        entry = request.entry

        if entry is None:
            entry = float(
                candles[-1].close
            )

        # ------------------------------------------------------
        # 5. QUANT PIPELINE
        # ------------------------------------------------------

        result = self.pipeline.run(
            candles=candles,
            symbol=request.symbol,
            market=request.market,
            timeframe=request.timeframe,
            capital=request.capital,
            entry=entry,
            stop_price=request.stop_price,
            tick_size=request.tick_size,
            wins=request.wins,
            losses=request.losses,
        )

        # ------------------------------------------------------
        # 6. RESPONSE
        # ------------------------------------------------------

        return {
            "status": "VALID",

            # Data information
            "data_source": data_source,
            "candles_count": len(candles),
            "volume_sum": float(volume_sum),
            "last_price": float(
                candles[-1].close
            ),

            # Market
            "symbol": result.symbol,
            "market": result.market,
            "timeframe": result.timeframe,

            # Volume Profile
            "profile": self._serialize(
                result.profile
            ),

            # Profile Dynamics
            "dynamics": self._serialize(
                result.dynamics
            ),

            # Market State
            "state": self._serialize(
                result.state
            ),

            # Historical Probability
            "probability": self._serialize(
                result.probability
            ),

            # Expected Value
            "expected_value_r": float(
                result.expected_value_r
            ),

            # Signal
            "signal": self._serialize(
                result.signal
            ),

            # Risk
            "risk": self._serialize(
                result.risk
            ),
        }
