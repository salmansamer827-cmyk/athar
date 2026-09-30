import os
import requests
import sqlite3
from datetime import datetime, timedelta, timezone

TRON_API = "https://api.trongrid.io"

USDT_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

RECEIVER = os.getenv(
    "USDT_RECEIVER_ADDRESS",
    "TFz7CLmoTZXcCpF6EMyfhp5nQQay6bB3wb"
)

PRICE = float(os.getenv("SUBSCRIPTION_PRICE_USDT", "10"))
DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))
DATABASE = os.getenv("DATABASE_PATH", "signal_saas.db")


def get_transaction(txid: str):
    url = f"{TRON_API}/v1/transactions/{txid}"

    response = requests.get(
        url,
        timeout=15
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("data"):
        return None

    return data["data"][0]


def get_trc20_transfers(txid: str):
    url = f"{TRON_API}/v1/transactions/{txid}/events"

    response = requests.get(
        url,
        timeout=15
    )

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("data", [])


def verify_usdt_payment(txid: str):
    tx = get_transaction(txid)

    if not tx:
        return {
            "valid": False,
            "reason": "Transaction not found"
        }

    contract_data = tx.get("raw_data", {}).get("contract", [])

    if not contract_data:
        return {
            "valid": False,
            "reason": "Invalid transaction"
        }

    events = get_trc20_transfers(txid)

    for event in events:
        if event.get("event") != "Transfer":
            continue

        result = event.get("result", {})

        from_address = result.get("from")
        to_address = result.get("to")
        value = result.get("value")

        if not from_address or not to_address or not value:
            continue

        if to_address != RECEIVER:
            continue

        amount = int(value) / 1_000_000

        if amount < PRICE:
            continue

        return {
            "valid": True,
            "txid": txid,
            "from": from_address,
            "to": to_address,
            "amount": amount,
            "network": "TRC20"
        }

    return {
        "valid": False,
        "reason": "No matching USDT payment found"
    }


def txid_already_used(txid: str):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM payments
        WHERE txid = ?
        AND status = 'CONFIRMED'
        """,
        (txid,)
    )

    result = cur.fetchone()

    conn.close()

    return result is not None


def activate_subscription(user_id: int, txid: str):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    now = datetime.now(timezone.utc)

    cur.execute(
        """
        SELECT expires_at
        FROM subscriptions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    row = cur.fetchone()

    if row and row[0]:
        try:
            current_expiry = datetime.fromisoformat(row[0])

            if current_expiry > now:
                start = current_expiry
            else:
                start = now

        except Exception:
            start = now
    else:
        start = now

    expiry = start + timedelta(days=DAYS)

    cur.execute(
        """
        INSERT INTO subscriptions
        (
            user_id,
            plan,
            status,
            starts_at,
            expires_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "MONTHLY",
            "ACTIVE",
            start.isoformat(),
            expiry.isoformat()
        )
    )

    conn.commit()
    conn.close()

    return expiry.isoformat()
