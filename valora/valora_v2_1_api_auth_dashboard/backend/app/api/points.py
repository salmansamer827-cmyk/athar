from decimal import Decimal, ROUND_DOWN
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/points", tags=["points"])

POINTS_PER_USDT = Decimal("10000")
PRICE_PER_MILLION = Decimal("100")


class PointQuote(BaseModel):
    usdt_amount: Decimal


@router.post("/quote")
def quote_points(data: PointQuote):

    if data.usdt_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="USDT amount must be greater than zero",
        )

    points = (
        data.usdt_amount * POINTS_PER_USDT
    ).quantize(
        Decimal("1"),
        rounding=ROUND_DOWN,
    )

    return {
        "usdt": str(data.usdt_amount),
        "points": str(points),
        "points_per_usdt": str(POINTS_PER_USDT),
        "price_per_million_points": str(
            PRICE_PER_MILLION
        ),
    }
