from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Customer,
    Subscription,
)


def utc_now():
    return datetime.now(timezone.utc)


def activate_subscription(
    db: Session,
    customer: Customer,
    price_usdt: Decimal | None = None,
):
    now = utc_now()

    price = (
        price_usdt
        if price_usdt is not None
        else settings.PRICE_USDT
    )

    existing = db.query(Subscription).filter(
        Subscription.customer_id == customer.id,
        Subscription.status == "ACTIVE",
    ).order_by(
        Subscription.expires_at.desc()
    ).first()

    if existing and existing.expires_at > now:
        starts_at = existing.expires_at
    else:
        starts_at = now

    expires_at = starts_at + timedelta(
        days=settings.SUBSCRIPTION_DAYS
    )

    subscription = Subscription(
        customer_id=customer.id,
        plan=settings.PRODUCT_NAME,
        price_usdt=price,
        starts_at=starts_at,
        expires_at=expires_at,
        status="ACTIVE",
        auto_renew=False,
    )

    customer.status = "ACTIVE"

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


def get_active_subscription(
    db: Session,
    customer_id: int
):
    now = utc_now()

    subscription = db.query(
        Subscription
    ).filter(
        Subscription.customer_id == customer_id,
        Subscription.status == "ACTIVE",
        Subscription.expires_at > now,
    ).order_by(
        Subscription.expires_at.desc()
    ).first()

    return subscription


def expire_subscriptions(db: Session):
    now = utc_now()

    subscriptions = db.query(
        Subscription
    ).filter(
        Subscription.status == "ACTIVE",
        Subscription.expires_at <= now,
    ).all()

    for subscription in subscriptions:
        subscription.status = "EXPIRED"

        customer = db.query(Customer).filter(
            Customer.id == subscription.customer_id
        ).first()

        if customer:
            customer.status = "EXPIRED"

    db.commit()

    return len(subscriptions)


def subscription_info(
    db: Session,
    customer_id: int
):
    subscription = get_active_subscription(
        db,
        customer_id
    )

    if not subscription:
        return None

    now = utc_now()

    remaining = (
        subscription.expires_at - now
    )

    return {
        "id": subscription.id,
        "plan": subscription.plan,
        "price_usdt": float(
            subscription.price_usdt
        ),
        "starts_at": subscription.starts_at,
        "expires_at": subscription.expires_at,
        "days_remaining": max(
            0,
            remaining.days
        ),
        "status": subscription.status,
    }
