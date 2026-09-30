from fastapi import APIRouter, HTTPException
from app.core.wallet_service import create_wallet, get_wallet

router = APIRouter(
    prefix="/wallet",
    tags=["wallet"]
)


@router.get("/{user_id}")
def wallet(user_id: str):

    try:
        create_wallet(user_id)
        return get_wallet(user_id)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
