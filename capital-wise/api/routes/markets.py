from fastapi import APIRouter, HTTPException
from api.services.binance_data import BinanceDataService

router = APIRouter(
    prefix="/api/v1/markets",
    tags=["Markets"],
)

service = BinanceDataService()


@router.get("/symbols")
def symbols():
    try:
        result = service.fetch_symbols()

        return {
            "status": "VALID",
            "count": len(result),
            "symbols": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "ERROR",
                "error": "SYMBOL_DISCOVERY_FAILED",
                "message": str(exc),
            },
        )


@router.get("/ohlcv")
def ohlcv(
    symbol: str,
    timeframe: str = "15m",
    limit: int = 200,
):
    try:
        candles = service.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            market="CRYPTO",
        )

        return {
            "status": "VALID",
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(candles),
            "candles": [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "ERROR",
                "error": "OHLCV_FETCH_FAILED",
                "message": str(exc),
            },
        )
