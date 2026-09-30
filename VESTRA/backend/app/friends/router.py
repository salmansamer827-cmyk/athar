from fastapi import APIRouter

router = APIRouter(
    prefix="/api/friends",
    tags=["Friends"],
)


@router.get("")
def friends():
    return {
        "status": "ok",
        "section": "friends",
        "friends": [],
        "requests": [],
    }
