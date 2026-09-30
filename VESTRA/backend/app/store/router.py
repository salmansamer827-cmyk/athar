from fastapi import APIRouter

router = APIRouter(
    prefix="/api/store",
    tags=["Store"],
)


@router.get("")
def store():
    return {
        "status": "ok",
        "section": "store",
        "points": {
            "10_000_000_points_usd": 1000,
            "points_per_usd": 10_000,
        },
        "products": [],
    }
