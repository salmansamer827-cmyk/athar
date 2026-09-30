from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.markets import router as markets_router
from api.routes.quant import router as quant_router
from api.routes.markets import router as markets_router


app = FastAPI(
    title="CAPITAL WISE API",
    description="Quantitative Trading Analytics API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "application": "CAPITAL WISE",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


app.include_router(quant_router)
app.include_router(markets_router)
