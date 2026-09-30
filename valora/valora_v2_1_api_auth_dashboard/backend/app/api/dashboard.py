from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def dashboard_summary():
    # Development response. Production reads the reconciled database.
    return {
        "portfolio": {
            "total_value": "100.800000",
            "principal": "100.000000",
            "profit": "0.800000",
            "roi_percent": "0.800000",
        },
        "wallets": {
            "usdt": "100.000000",
            "usdc": "0.000000",
            "points": "1000000",
        },
        "investment": {
            "provider": "BINANCE",
            "product": "RWUSD",
            "status": "ACTIVE",
            "nav": "100.800000",
            "last_synced_at": None,
        },
    }
