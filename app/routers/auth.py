from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.users import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.security import create_access_token, hash_password, verify_password

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
    return TokenResponse(access_token=access_token)
