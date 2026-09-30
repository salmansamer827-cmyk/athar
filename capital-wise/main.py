from fastapi import FastAPI

app = FastAPI(
    title="Capital Wise",
    version="0.1.0",
    description="Multi-Asset Market Intelligence Platform"
)


@app.get("/")
def root():
    return {
        "project": "Capital Wise",
        "version": "0.1.0",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
