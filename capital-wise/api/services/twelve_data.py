from __future__ import annotations

import os
import requests

from dotenv import load_dotenv

from core.data.models import OHLCV


load_dotenv()


class TwelveDataService:
    """
    CAPITAL WISE

    Twelve Data market-data adapter.

    Converts Twelve Data time-series responses
    into the internal CAPITAL WISE OHLCV model.
    """

    BASE_URL = "https://api.twelvedata.com/time_series"

    INTERVAL_MAP = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "45m": "45min",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "8h": "8h",
        "1d": "1day",
        "1w": "1week",
        "1M": "1month",
    }

    def __init__(self):
        self.api_key = os.getenv(
            "TWELVEDATA_API_KEY"
        )

        if not self.api_key:
            raise RuntimeError(
                "TWELVEDATA_API_KEY is not configured"
            )

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 100,
        market: str = "UNKNOWN",
    ) -> list[OHLCV]:

        if limit < 2:
            raise ValueError(
                "limit must be >= 2"
            )

        if limit > 5000:
            limit = 5000

        interval = self.INTERVAL_MAP.get(
            timeframe
        )

        if interval is None:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": limit,
            "apikey": self.api_key,
            "order": "ASC",
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") == "error":
            raise RuntimeError(
                data.get(
                    "message",
                    "Twelve Data API error",
                )
            )

        values = data.get("values")

        if not values:
            raise RuntimeError(
                "Twelve Data returned no candles"
            )

        candles = []

        for row in values:

            timestamp = self._timestamp(
                row["datetime"]
            )

            candles.append(
                OHLCV(
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(
                        row.get("volume", 0)
                        or 0
                    ),
                    symbol=symbol,
                    market=market,
                    timeframe=timeframe,
                )
            )

        return candles

    @staticmethod
    def _timestamp(value: str) -> int:
        """
        Convert Twelve Data datetime into
        Unix milliseconds.

        Twelve Data may return either:
        YYYY-MM-DD HH:MM:SS
        or timezone-aware values.
        """

        from datetime import datetime, timezone

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
        ]

        for fmt in formats:

            try:

                dt = datetime.strptime(
                    value,
                    fmt,
                )

                if dt.tzinfo is None:
                    dt = dt.replace(
                        tzinfo=timezone.utc
                    )

                return int(
                    dt.timestamp() * 1000
                )

            except ValueError:
                continue

        raise ValueError(
            f"Unsupported datetime format: {value}"
        )
