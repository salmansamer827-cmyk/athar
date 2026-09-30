from sqlalchemy import Column, Integer, Numeric, ForeignKey
from app.db.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    vestra_points = Column(
        Numeric(30, 8),
        default=0,
        nullable=False,
    )

    usdt_balance = Column(
        Numeric(30, 8),
        default=0,
        nullable=False,
    )

    usdc_balance = Column(
        Numeric(30, 8),
        default=0,
        nullable=False,
    )
