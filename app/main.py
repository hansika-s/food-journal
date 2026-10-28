from datetime import datetime
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, User
from app.security import create_access_token, decode_access_token, hash_password, verify_password


# Post schemas
class PostCreate(BaseModel):
    restaurant_name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    cuisine: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    notes: str = ""


class PostUpdate(BaseModel):
    restaurant_name: str | None = Field(default=None, min_length=1)
    city: str | None = Field(default=None, min_length=1)
    cuisine: str | None = Field(default=None, min_length=1)
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = None
    notes: str | None = None


class PostResponse(PostCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


app = FastAPI()


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.post("/posts", status_code=201)
def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    new_post = Post(**post.model_dump(), user_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return PostResponse.model_validate(new_post)


@app.get("/posts")
def list_posts(
    city: str | None = None,
    cuisine: str | None = None,
    min_rating: int | None = Query(default=None, ge=1, le=5),
    tag: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    statement = select(Post).where(Post.user_id == current_user.id)

    if city is not None:
        statement = statement.where(Post.city == city)

    if cuisine is not None:
        statement = statement.where(Post.cuisine == cuisine)

    if min_rating is not None:
        statement = statement.where(Post.rating >= min_rating)

    if tag is not None:
        statement = statement.where(Post.tags.contains([tag]))

    result = db.scalars(
        statement.order_by(Post.created_at).offset(skip).limit(limit)
    ).all()
    return [PostResponse.model_validate(post) for post in result]


@app.get("/posts/{post_id}")
def get_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return PostResponse.model_validate(post)


@app.patch("/posts/{post_id}")
def update_post(
    post_id: UUID,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    updates = post_update.model_dump(exclude_unset=True)
    if any(value is None for value in updates.values()):
        raise HTTPException(status_code=422, detail="Post fields cannot be null")

    for field, value in updates.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return PostResponse.model_validate(post)


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()


@app.post("/signup", status_code=201)
def user_signup(
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
        raise HTTPException(status_code=409, detail="Email already registered")

    db.refresh(new_user)
    return UserResponse.model_validate(new_user)


@app.post("/login")
def user_login(
    user: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    db_user = db.scalar(select(User).where(User.email == user.email.lower()))
    if db_user is None or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(db_user.id)
    return TokenResponse(access_token=access_token)
