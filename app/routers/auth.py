from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cookies import delete_session_cookie, set_session_cookie
from app.database import get_db
from app.dependencies import csrf_matches, get_cookie_session
from app.models import User, UserSession
from app.schemas.users import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    SessionResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.security import create_access_token, hash_password
from app.services import sessions
from app.services.auth import (
    InvalidRefreshTokenError,
    authenticate_user,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    new_user = User(
        email=user.email.lower(),
        password_hash=hash_password(user.password),
        name=user.name,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    db.refresh(new_user)
    return UserResponse.model_validate(new_user)


@router.post("/login")
def login_user(
    user: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> LoginResponse:
    db_user = authenticate_user(db, user.email, user.password)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(db_user.id)
    refresh_token = create_refresh_token(db, db_user.id)
    session_id, csrf_token = sessions.create_session(db, db_user.id)
    set_session_cookie(response, session_id)
    return LoginResponse(access_token=access_token, refresh_token=refresh_token, csrf_token=csrf_token)


# Browsers call this on page load to find out who is logged in. Needs the session cookie, no CSRF token.
@router.get("/session")
def read_session(
    user_session: UserSession = Depends(get_cookie_session),
    db: Session = Depends(get_db),
) -> SessionResponse:
    user = db.get(User, user_session.user_id)
    return SessionResponse(user=UserResponse.model_validate(user), csrf_token=user_session.csrf_token)


@router.post("/refresh")
def refresh_tokens(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        user_id, new_refresh_token = rotate_refresh_token(db, request.refresh_token)
    except InvalidRefreshTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return TokenResponse(access_token=create_access_token(user_id), refresh_token=new_refresh_token)


# Ends whatever is sent: a refresh token in the body (API clients) and/or the session cookie (browsers).
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: RefreshTokenRequest | None = None,
    session_id: str | None = Cookie(default=None),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: Session = Depends(get_db),
) -> Response:
    if request is not None:
        revoke_refresh_token(db, request.refresh_token)

    if session_id is not None:
        user_session = sessions.get_session(db, session_id)
        if user_session is not None and not csrf_matches(user_session.csrf_token, csrf_header):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing or invalid")
        sessions.delete_session(db, session_id)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    delete_session_cookie(response)
    return response
