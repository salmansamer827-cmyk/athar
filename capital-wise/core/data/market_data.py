from __future__ import annotations

import ccxt
import pandas as pd


class MarketDataEngine:
    """
    Capital Wise Market Data Engine

    مسؤول عن جلب OHLCV
    وتوحيد بيانات الأسواق داخل النظام.
    """

    def __init__(self):
        self.exchange = ccxt.binance({
            "enableRateLimit": True,
        })

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 500,
    ) -> pd.DataFrame:

        data = self.exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if not data:
            raise ValueError(f"No market data returned for {symbol}")

        df = pd.DataFrame(
            data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            unit="ms",
            utc=True,
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        df[numeric_columns] = df[numeric_columns].astype(float)

        return df
