from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.wallet import Wallet


router = APIRouter(
    prefix="/api/wallet",
    tags=["Wallet"],
)


@router.get("/{user_id}")
def get_wallet(
    user_id: int,
    db: Session = Depends(get_db),
):
    wallet = db.query(Wallet).filter(
        Wallet.user_id == user_id
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found",
        )

    return {
        "user_id": user_id,
        "balances": {
            "vestra_points": float(wallet.vestra_points),
            "usdt": float(wallet.usdt_balance),
            "usdc": float(wallet.usdc_balance),
        },
    }
