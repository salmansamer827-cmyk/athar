from fastapi import FastAPI

from .api.auth import router as auth_router
from .api.dashboard import router as dashboard_router
from .api.wallet import router as wallet_router
from .api.points import router as points_router
from .api.chat import router as chat_router
from .api.live import router as live_router


app = FastAPI(
    title="VALORA API",
    version="2.2.0",
)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(wallet_router)
app.include_router(points_router)
app.include_router(chat_router)
app.include_router(live_router)


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "VALORA",
        "version": "2.2.0",
    }
