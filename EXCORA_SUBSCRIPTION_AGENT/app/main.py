import os

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from dotenv import load_dotenv

from .database import (
    init_database,
    get_connection,
    save_payment,
    activate_subscription
)

from .subscriptions import (
    PLANS,
    create_plan_subscription
)

from .payments import verify_erc20_payment


load_dotenv()

app = FastAPI(
    title="EXCORA Subscription Agent",
    version="1.0.0"
)

templates = Jinja2Templates(
    directory="app/templates"
)


@app.on_event("startup")
def startup():
    init_database()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "pro_price": PLANS["PRO"]["price"],
            "three_price": PLANS["PRO_3_MONTHS"]["price"],
            "yearly_price": PLANS["PRO_YEARLY"]["price"]
        }
    )


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "EXCORA Subscription Agent",
        "version": "1.0.0"
    }


@app.post("/subscribe")
def subscribe(
    name: str,
    email: str,
    plan: str,
    wallet_address: str = ""
):

    result = create_plan_subscription(
        name=name,
        email=email,
        plan=plan,
        wallet_address=wallet_address
    )

    return {
        "status": "PENDING_PAYMENT",
        "customer": result["customer"],
        "subscription_id":
            result["subscription_id"],
        "plan": result["plan"],
        "network": "Arbitrum One",
        "accepted_assets": [
            "USDT",
            "USDC"
        ],
        "payment_wallet":
            os.getenv("PAYMENT_WALLET")
    }


@app.post("/payment/verify")
def verify_payment(
    subscription_id: int,
    tx_hash: str
):

    conn = get_connection()

    subscription = conn.execute("""
        SELECT *
        FROM subscriptions
        WHERE id = ?
    """, (subscription_id,)).fetchone()

    conn.close()

    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    result = verify_erc20_payment(
        tx_hash,
        float(subscription["price_usd"])
    )

    if not result.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=result.get("reason")
        )

    customer_id = subscription["customer_id"]

    save_payment(
        customer_id=customer_id,
        subscription_id=subscription_id,
        tx_hash=tx_hash,
        asset=result["asset"],
        amount=result["amount"],
        status="CONFIRMED"
    )

    plan = subscription["plan"]

    if plan == "PRO":
        months = 1
    elif plan == "PRO_3_MONTHS":
        months = 3
    elif plan == "PRO_YEARLY":
        months = 12
    else:
        months = 1

    activate_subscription(
        subscription_id,
        months
    )

    return {
        "status": "ACTIVE",
        "subscription_id": subscription_id,
        "asset": result["asset"],
        "amount": result["amount"],
        "network": "Arbitrum One"
    }


@app.get("/admin/subscribers")
def subscribers(
    x_admin_token: str = Header(default="")
):

    admin_token = os.getenv("ADMIN_TOKEN")

    if x_admin_token != admin_token:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            c.id AS customer_id,
            c.name,
            c.email,
            c.wallet_address,
            s.id AS subscription_id,
            s.plan,
            s.price_usd,
            s.status,
            s.started_at,
            s.expires_at
        FROM customers c
        LEFT JOIN subscriptions s
            ON c.id = s.customer_id
        ORDER BY c.id DESC
    """).fetchall()

    conn.close()

    return {
        "count": len(rows),
        "subscribers": [
            dict(row)
            for row in rows
        ]
    }
