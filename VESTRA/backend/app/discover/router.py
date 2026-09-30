from fastapi import APIRouter

router = APIRouter(
    prefix="/api/discover",
    tags=["Discover"],
)


@router.get("")
def discover():
    return {
        "status": "ok",
        "section": "discover",
        "items": [],
    }
