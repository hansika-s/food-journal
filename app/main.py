from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post


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


app = FastAPI()


@app.post("/posts", status_code=201)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
) -> PostResponse:
    new_post = Post(**post.model_dump())
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
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    statement = select(Post)

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
    db: Session = Depends(get_db),
) -> PostResponse:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return PostResponse.model_validate(post)


@app.patch("/posts/{post_id}")
def update_post(
    post_id: UUID,
    post_update: PostUpdate,
    db: Session = Depends(get_db),
) -> PostResponse:
    post = db.get(Post, post_id)
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
def delete_post(post_id: UUID, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    
    db.delete(post)
    db.commit()
        
    
