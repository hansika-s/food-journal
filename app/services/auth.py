import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.models import RefreshToken, User
from app.security import verify_password


class InvalidRefreshTokenError(Exception):
    pass


# Returns the SHA-256 hex digest of a token. Only this hash is stored.
def hash_refresh_token(token: str) -> str:
    sha256 = hashlib.sha256()

    sha256.update(token.encode())
    return sha256.hexdigest()


# Creates a refresh token for the user, stores its hash, and returns the raw token.
def create_refresh_token(db: Session, user_id: UUID) -> str:
    token = secrets.token_urlsafe(32)
    new_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(new_token)
    db.commit()

    return token


# Replaces a refresh token with a new one. Reusing a revoked token revokes all of the user's tokens.
def rotate_refresh_token(db: Session, token: str) -> tuple[UUID, str]:
    refresh_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(token)))
    now = datetime.now(timezone.utc)

    if refresh_token is None:
        raise InvalidRefreshTokenError()

    if refresh_token.revoked_at is not None:
        revoke_all_refresh_tokens(db, refresh_token.user_id)
        raise InvalidRefreshTokenError()

    if refresh_token.expires_at <= now:
        raise InvalidRefreshTokenError()

    refresh_token.revoked_at = now
    new_refresh_token = create_refresh_token(db, refresh_token.user_id)
    return (refresh_token.user_id, new_refresh_token)


# Revokes one refresh token, used by logout. Does nothing if the token is unknown.
def revoke_refresh_token(db: Session, token: str) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(token), RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()


# Revokes all of a user's active refresh tokens, used by logout everywhere and reuse detection.
def revoke_all_refresh_tokens(db: Session, user_id: UUID) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()


# Returns the user if the email and password match, otherwise None. Shared by the JSON and form login routes.
def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
