from fastapi import APIRouter

router = APIRouter(prefix="/live", tags=["live"])


@router.get("/featured")
def featured():

    return {
        "guest_access": True,
        "streams": [
            {
                "id": "demo-live-001",
                "title": "VALORA LIVE",
                "status": "DEMO",
                "viewers": 0,
            }
        ],
    }
