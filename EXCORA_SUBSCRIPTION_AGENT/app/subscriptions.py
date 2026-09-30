import os

from .database import (
    get_customer_by_email,
    create_customer,
    create_subscription
)

PRO_PRICE = float(os.getenv("PRO_PRICE", "19"))
THREE_MONTHS_PRICE = float(
    os.getenv("PRO_3_MONTHS_PRICE", "49")
)
YEARLY_PRICE = float(
    os.getenv("PRO_YEARLY_PRICE", "149")
)


PLANS = {
    "PRO": {
        "name": "EXCORA PRO",
        "price": PRO_PRICE,
        "months": 1
    },

    "PRO_3_MONTHS": {
        "name": "EXCORA PRO 3 MONTHS",
        "price": THREE_MONTHS_PRICE,
        "months": 3
    },

    "PRO_YEARLY": {
        "name": "EXCORA PRO YEARLY",
        "price": YEARLY_PRICE,
        "months": 12
    }
}


def register_customer(name, email, wallet_address=None):
    existing = get_customer_by_email(email)

    if existing:
        return existing

    return create_customer(
        name,
        email,
        wallet_address
    )


def create_plan_subscription(
    name,
    email,
    plan,
    wallet_address=None
):
    if plan not in PLANS:
        raise ValueError("Invalid plan")

    customer = register_customer(
        name,
        email,
        wallet_address
    )

    selected = PLANS[plan]

    subscription_id = create_subscription(
        customer_id=customer["id"],
        plan=plan,
        price=selected["price"]
    )

    return {
        "customer": customer,
        "subscription_id": subscription_id,
        "plan": selected
    }
