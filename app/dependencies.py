import secrets
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserSession
from app.security import decode_access_token
from app.services import sessions

# auto_error=False so a missing header doesn't fail here. The session cookie can be used instead.
bearer_scheme = HTTPBearer(auto_error=False)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


# Raised when a browser page needs a logged-in user and there isn't one.
# main.py turns this into a redirect to /login.
class LoginRequiredError(Exception):
    pass


# Accepts a bearer token (API clients) or the session cookie (browsers).
# Cookie requests that change data must also send the session's CSRF token in the X-CSRF-Token header.
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session_id: str | None = Cookie(default=None),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: Session = Depends(get_db),
) -> User:
    if credentials is not None:
        return user_from_access_token(db, credentials.credentials)

    user_session = sessions.get_session(db, session_id) if session_id is not None else None
    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if request.method not in SAFE_METHODS and not csrf_matches(user_session.csrf_token, csrf_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing or invalid")
    return db.get(User, user_session.user_id)


def user_from_access_token(db: Session, token: str) -> User:
    try:
        user_id = decode_access_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# True when the given token matches the expected one. Compares in constant time so timing can't reveal it.
def csrf_matches(expected: str, given: str | None) -> bool:
    return given is not None and secrets.compare_digest(expected, given)


def get_current_web_session(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UserSession:
    user_session = sessions.get_session(db, session_id) if session_id is not None else None
    if user_session is None:
        raise LoginRequiredError()
    return user_session
