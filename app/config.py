import os

from dotenv import load_dotenv

load_dotenv()


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DATABASE_URL = required_env("DATABASE_URL")
JWT_SECRET_KEY = required_env("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
