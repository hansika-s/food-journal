import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Argon2 with the library's recommended settings. Created once and reused.
hasher = PasswordHash.recommended()


# Returns the hash, which includes the salt and settings
def hash_password(password: str) -> str:
    return hasher.hash(password)


# Returns True if the plain password matches the stored hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hasher.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    return payload["sub"]
