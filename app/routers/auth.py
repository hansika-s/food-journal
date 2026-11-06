from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.users import LoginRequest, RefreshTokenRequest, TokenResponse, UserCreate, UserResponse
from app.security import create_access_token, hash_password, verify_password
from app.services.auth import create_refresh_token, revoke_refresh_token, rotate_refresh_token

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
    db: Session = Depends(get_db),
) -> TokenResponse:
    db_user = db.scalar(select(User).where(User.email == user.email.lower()))
    if db_user is None or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(db_user.id)
    refresh_token = create_refresh_token(db, db_user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh")
def refresh_tokens(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user_id, new_refresh_token = rotate_refresh_token(db, request.refresh_token)
    return TokenResponse(access_token=create_access_token(user_id), refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(db, request.refresh_token)
