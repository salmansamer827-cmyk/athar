from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey
from datetime import datetime

from app.db.database import Base


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    amount = Column(
        Numeric(30, 8),
        nullable=False,
    )

    transaction_type = Column(
        String(30),
        nullable=False,
    )

    reference = Column(
        String(100),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
