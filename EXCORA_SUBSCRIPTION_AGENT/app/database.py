import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH", "data/excora.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            wallet_address TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            price_usd REAL NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT,
            expires_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            subscription_id INTEGER,
            tx_hash TEXT UNIQUE NOT NULL,
            asset TEXT NOT NULL,
            network TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(subscription_id) REFERENCES subscriptions(id)
        )
    """)

    conn.commit()
    conn.close()


def create_customer(name, email, wallet_address=None):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    conn.execute("""
        INSERT OR IGNORE INTO customers
        (name, email, wallet_address, created_at)
        VALUES (?, ?, ?, ?)
    """, (name, email, wallet_address, now))

    conn.commit()

    row = conn.execute(
        "SELECT * FROM customers WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    return dict(row)


def get_customer_by_email(email):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM customers WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def create_subscription(customer_id, plan, price):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    cursor = conn.execute("""
        INSERT INTO subscriptions
        (customer_id, plan, price_usd, status, created_at)
        VALUES (?, ?, ?, 'PENDING', ?)
    """, (customer_id, plan, price, now))

    conn.commit()

    subscription_id = cursor.lastrowid

    conn.close()

    return subscription_id


def save_payment(
    customer_id,
    subscription_id,
    tx_hash,
    asset,
    amount,
    status
):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    conn.execute("""
        INSERT INTO payments
        (customer_id, subscription_id, tx_hash, asset,
         network, amount, status, created_at)
        VALUES (?, ?, ?, ?, 'Arbitrum One', ?, ?, ?)
    """, (
        customer_id,
        subscription_id,
        tx_hash,
        asset,
        amount,
        status,
        now
    ))

    conn.commit()
    conn.close()


def activate_subscription(subscription_id, months=1):
    from datetime import timedelta

    conn = get_connection()

    now = datetime.utcnow()

    row = conn.execute("""
        SELECT * FROM subscriptions
        WHERE id = ?
    """, (subscription_id,)).fetchone()

    if not row:
        conn.close()
        return False

    start = now

    if months == 1:
        days = 30
    elif months == 3:
        days = 90
    elif months == 12:
        days = 365
    else:
        days = 30

    expires = start + timedelta(days=days)

    conn.execute("""
        UPDATE subscriptions
        SET status = 'ACTIVE',
            started_at = ?,
            expires_at = ?
        WHERE id = ?
    """, (
        start.isoformat(),
        expires.isoformat(),
        subscription_id
    ))

    conn.commit()
    conn.close()

    return True
