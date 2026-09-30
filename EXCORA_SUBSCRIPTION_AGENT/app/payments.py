import os
import requests

from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv(
    "ARBITRUM_RPC_URL",
    "https://arb1.arbitrum.io/rpc"
)

PAYMENT_WALLET = os.getenv("PAYMENT_WALLET", "").lower()

# Arbitrum One
# Native USDC
USDC_CONTRACT = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831".lower()

# USDT
USDT_CONTRACT = "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9".lower()

TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa"
    "952ba7f163c4a11628f55a5df523b3ef"
)


def rpc(method, params):
    response = requests.post(
        RPC_URL,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        },
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return data["result"]


def hex_to_int(value):
    return int(value, 16)


def decode_address(topic):
    return "0x" + topic[-40:].lower()


def verify_erc20_payment(tx_hash, expected_amount):
    tx_hash = tx_hash.strip()

    if not tx_hash.startswith("0x"):
        return {
            "valid": False,
            "reason": "Invalid transaction hash"
        }

    receipt = rpc(
        "eth_getTransactionReceipt",
        [tx_hash]
    )

    if not receipt:
        return {
            "valid": False,
            "reason": "Transaction not found"
        }

    if receipt.get("status") != "0x1":
        return {
            "valid": False,
            "reason": "Transaction failed"
        }

    logs = receipt.get("logs", [])

    for log in logs:

        address = log.get("address", "").lower()

        if address not in {
            USDC_CONTRACT,
            USDT_CONTRACT
        }:
            continue

        topics = log.get("topics", [])

        if len(topics) < 3:
            continue

        if topics[0].lower() != TRANSFER_TOPIC:
            continue

        recipient = decode_address(topics[2])

        if recipient != PAYMENT_WALLET:
            continue

        raw_amount = hex_to_int(log.get("data", "0x0"))

        amount = raw_amount / 1_000_000

        asset = (
            "USDC"
            if address == USDC_CONTRACT
            else "USDT"
        )

        if amount + 0.000001 < expected_amount:
            return {
                "valid": False,
                "reason": "Payment amount is too low",
                "asset": asset,
                "amount": amount
            }

        return {
            "valid": True,
            "asset": asset,
            "amount": amount,
            "tx_hash": tx_hash,
            "network": "Arbitrum One"
        }

    return {
        "valid": False,
        "reason": "No matching USDT/USDC payment found"
    }
