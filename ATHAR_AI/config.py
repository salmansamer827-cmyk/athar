import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "ATHAR AI"
VERSION = "1.0.0"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://api.openai.com/v1"
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6"
)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "data/athar.db"
)

MAX_STEPS = int(
    os.getenv("MAX_STEPS", "10")
)

ALLOW_SHELL = os.getenv(
    "ALLOW_SHELL",
    "false"
).lower() == "true"

WORKSPACE = os.path.abspath(
    os.getenv("WORKSPACE", ".")
)
