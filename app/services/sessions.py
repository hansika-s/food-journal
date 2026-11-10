import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import SESSION_EXPIRE_DAYS
from app.models import UserSession


# Returns the SHA-256 hex digest of a session ID. Only this hash is stored.
def hash_session_id(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()


# Creates a session for the user and returns the raw session ID, which goes in the cookie.
def create_session(db: Session, user_id: UUID) -> str:
    session_id = secrets.token_urlsafe(32)
    db.add(
        UserSession(
            user_id=user_id,
            session_hash=hash_session_id(session_id),
            csrf_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS),
        )
    )
    db.commit()
    return session_id


# Returns the session row for a valid session ID, or None if the session is unknown or expired.
def get_session(db: Session, session_id: str) -> UserSession | None:
    user_session = db.scalar(select(UserSession).where(UserSession.session_hash == hash_session_id(session_id)))
    if user_session is None or user_session.expires_at <= datetime.now(timezone.utc):
        return None
    return user_session


# Deletes a session, used by logout. Does nothing if the session is unknown.
def delete_session(db: Session, session_id: str) -> None:
    db.execute(delete(UserSession).where(UserSession.session_hash == hash_session_id(session_id)))
    db.commit()
