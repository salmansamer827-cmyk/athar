from __future__ import annotations

import requests

from core.data.models import OHLCV


class BinanceDataService:
    """
    CAPITAL WISE
    Direct Binance REST market-data adapter.

    No CCXT dependency.
    Returns real OHLCV + volume.
    """

    BASE_URL = "https://api.binance.com/api/v3/klines"

    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M",
    }

    def fetch_symbols(self) -> list[str]:
        """
        Return active Binance Spot USDT symbols.
        """

        url = "https://api.binance.com/api/v3/exchangeInfo"

        response = requests.get(
            url,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        symbols = []

        for item in data.get("symbols", []):
            if (
                item.get("status") == "TRADING"
                and item.get("quoteAsset") == "USDT"
                and item.get("isSpotTradingAllowed") is True
            ):
                base = item.get("baseAsset")
                quote = item.get("quoteAsset")

                if base and quote:
                    symbols.append(f"{base}/{quote}")

        return sorted(set(symbols))

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 100,
        market: str = "CRYPTO",
    ) -> list[OHLCV]:

        if limit < 2:
            raise ValueError("limit must be >= 2")

        limit = min(limit, 1000)

        interval = self.INTERVAL_MAP.get(timeframe)

        if interval is None:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        binance_symbol = (
            symbol.replace("/", "")
            .replace("-", "")
            .upper()
        )

        params = {
            "symbol": binance_symbol,
            "interval": interval,
            "limit": limit,
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise RuntimeError(
                f"Binance API error: {data}"
            )

        candles = []

        for row in data:

            candles.append(
                OHLCV(
                    timestamp=int(row[0]),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                    symbol=symbol,
                    market=market,
                    timeframe=timeframe,
                )
            )

        return candles
