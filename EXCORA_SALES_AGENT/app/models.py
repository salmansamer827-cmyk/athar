from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)

    name = Column(String(200), nullable=True)
    email = Column(String(320), nullable=True)
    phone = Column(String(50), nullable=True)
    telegram_username = Column(String(100), nullable=True)

    source = Column(String(100), nullable=True)
    profile_url = Column(String(500), nullable=True)

    status = Column(
        String(50),
        default="NEW",
        nullable=False
    )

    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="lead",
        uselist=False
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)

    lead_id = Column(
        Integer,
        ForeignKey("leads.id"),
        nullable=True
    )

    name = Column(String(200), nullable=True)
    email = Column(String(320), nullable=True)
    phone = Column(String(50), nullable=True)
    telegram_username = Column(String(100), nullable=True)

    status = Column(
        String(50),
        default="NEW",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    lead = relationship(
        "Lead",
        back_populates="customer"
    )

    conversations = relationship(
        "Conversation",
        back_populates="customer"
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="customer"
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    channel = Column(
        String(50),
        nullable=False
    )

    direction = Column(
        String(20),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="conversations"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    plan = Column(
        String(100),
        default="EXCORA PRO",
        nullable=False
    )

    price_usdt = Column(
        Numeric(18, 6),
        nullable=False
    )

    starts_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    status = Column(
        String(50),
        default="ACTIVE",
        nullable=False
    )

    auto_renew = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="subscriptions"
    )

    payments = relationship(
        "Payment",
        back_populates="subscription"
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False
    )

    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id"),
        nullable=True
    )

    tx_hash = Column(
        String(100),
        unique=True,
        nullable=False
    )

    amount_usdt = Column(
        Numeric(18, 6),
        nullable=False
    )

    network = Column(
        String(50),
        nullable=False
    )

    recipient = Column(
        String(100),
        nullable=False
    )

    status = Column(
        String(50),
        default="PENDING",
        nullable=False
    )

    verified = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    subscription = relationship(
        "Subscription",
        back_populates="payments"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    actor = Column(
        String(100),
        nullable=False
    )

    action = Column(
        String(100),
        nullable=False
    )

    entity_type = Column(
        String(100),
        nullable=True
    )

    entity_id = Column(
        String(100),
        nullable=True
    )

    details = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
