from decimal import Decimal
from app.db.database import get_connection


ASSETS = ("USDT", "USDC", "POINTS")


def create_wallet(user_id):

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO wallets (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
                RETURNING wallet_id
                """,
                (user_id,)
            )

            wallet = cur.fetchone()

            if wallet:
                wallet_id = wallet["wallet_id"]
            else:
                cur.execute(
                    """
                    SELECT wallet_id
                    FROM wallets
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )

                wallet_id = cur.fetchone()["wallet_id"]

            for asset in ASSETS:

                cur.execute(
                    """
                    INSERT INTO wallet_balances
                    (wallet_id, asset)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (wallet_id, asset)
                )

            return wallet_id


def get_wallet(user_id):

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    wb.asset,
                    wb.available,
                    wb.locked
                FROM wallets w
                JOIN wallet_balances wb
                    ON wb.wallet_id = w.wallet_id
                WHERE w.user_id = %s
                ORDER BY wb.asset
                """,
                (user_id,)
            )

            rows = cur.fetchall()

            return [
                {
                    "asset": row["asset"],
                    "available": str(row["available"]),
                    "locked": str(row["locked"]),
                }
                for row in rows
            ]
