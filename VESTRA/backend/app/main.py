from app.wallet.router import router as wallet_router
from app.discover.router import router as discover_router
from app.store.router import router as store_router
from app.friends.router import router as friends_router
from fastapi import FastAPI

from app.db.database import Base, engine

from app.models import (
    User,
    Wallet,
    PointTransaction,
    Room,
    RoomMember,
    VoiceSeat,
    MicrophonePermission,
    SpeakingRequest,
)

from app.rooms.router import router as rooms_router


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="VESTRA API",
    version="0.3.0",
    description="VESTRA Global Digital Points Platform",
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(rooms_router)
app.include_router(discover_router)
app.include_router(store_router)
app.include_router(friends_router)
app.include_router(wallet_router)
# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "app": "VESTRA",
        "status": "online",
        "version": "0.3.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "vestra-api",
        "database": "sqlite",
    }


# ============================================================
# PUBLIC CONFIG
# ============================================================

@app.get("/api/config")
def config():
    return {
        "app": "VESTRA",

        "points": {
            "user": {
                "10_000_000_points_usd": 1000,
                "points_per_usd": 10_000,
            },
        },

        "assets": [
            "VESTRA_POINTS",
            "USDT",
            "USDC",
        ],

        "bottom_navigation": [
            "rooms",
            "discover",
            "store",
            "friends",
            "wallet",
        ],

        "rooms": {
            "voice_seats": True,
            "microphone_permissions": True,
            "speaking_requests": True,
        },
    }
