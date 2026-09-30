import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "EXCORA AI Sales Agent"
    APP_VERSION = "1.0.0"

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/excora_sales.db"
    )

    # Product
    PRODUCT_NAME = "EXCORA PRO"
    PRICE_USDT = Decimal(os.getenv("PRICE_USDT", "30"))
    MAX_DISCOUNT_PERCENT = Decimal(
        os.getenv("MAX_DISCOUNT_PERCENT", "5")
    )
    MIN_PRICE_USDT = Decimal(
        os.getenv("MIN_PRICE_USDT", "28.50")
    )
    SUBSCRIPTION_DAYS = int(
        os.getenv("SUBSCRIPTION_DAYS", "30")
    )

    # Payment
    PAYMENT_NETWORK = os.getenv(
        "PAYMENT_NETWORK",
        "arbitrum"
    )

    PAYMENT_ADDRESS = os.getenv(
        "PAYMENT_ADDRESS",
        ""
    )

    # Agent identity
    AGENT_NAME = os.getenv(
        "AGENT_NAME",
        "EXCORA AI Sales Agent"
    )

    OWNER_NAME = os.getenv(
        "OWNER_NAME",
        "EXCORA"
    )


settings = Settings()
