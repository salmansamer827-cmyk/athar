import sqlite3
import os

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv(
    "DATABASE_PATH",
    "data/excora.db"
)

conn = sqlite3.connect(DB_PATH)

conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT
        c.id,
        c.name,
        c.email,
        s.plan,
        s.status,
        s.price_usd,
        s.started_at,
        s.expires_at
    FROM customers c
    LEFT JOIN subscriptions s
        ON c.id = s.customer_id
    ORDER BY c.id DESC
""").fetchall()

print()
print("=" * 90)
print("              EXCORA SUBSCRIBERS")
print("=" * 90)

print(
    f"{'ID':<5}"
    f"{'NAME':<20}"
    f"{'EMAIL':<30}"
    f"{'PLAN':<18}"
    f"{'STATUS':<10}"
)

print("-" * 90)

for row in rows:

    print(
        f"{str(row['id']):<5}"
        f"{str(row['name'] or '')[:19]:<20}"
        f"{str(row['email'] or '')[:29]:<30}"
        f"{str(row['plan'] or ''):<18}"
        f"{str(row['status'] or ''):<10}"
    )

print("=" * 90)

conn.close()
