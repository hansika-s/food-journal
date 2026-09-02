from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


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
    id: UUID
    created_at: datetime


app = FastAPI()
posts: list[PostResponse] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/posts", status_code=201)
def create_post(post: PostCreate) -> PostResponse:
    new_post = PostResponse(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        **post.model_dump(),
    )
    posts.append(new_post)
    return new_post


@app.get("/posts")
def list_posts(
    city: str | None = None,
    cuisine: str | None = None,
    min_rating: int | None = Query(default=None, ge=1, le=5),
    tag: str | None = None,
    skip: int = Query(default= 0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    ) -> list[PostResponse]:
    filtered_posts = posts

    if city is not None:
        filtered_posts = [
            post for post in filtered_posts 
            if post.city == city
        ]
    
    if cuisine is not None:
        filtered_posts = [
            post for post in filtered_posts 
            if post.cuisine == cuisine
        ]

    if min_rating is not None:
        filtered_posts = [
            post for post in filtered_posts
            if post.rating >= min_rating
        ]

    if tag is not None:
        filtered_posts = [
            post for post in filtered_posts
            if tag in post.tags
        ]

    return filtered_posts[skip: skip + limit]


@app.get("/posts/{post_id}")
def get_post(post_id: UUID) -> PostResponse:
    for post in posts:
        if post.id == post_id:
            return post

    raise HTTPException(status_code=404, detail="Post not found")


@app.patch("/posts/{post_id}")
def update_post(post_id: UUID, post_update: PostUpdate) -> PostResponse:
    updates = post_update.model_dump(exclude_unset=True)

    for post in posts:
        if post.id == post_id:
            for field, value in updates.items():
                setattr(post, field, value)

            return post 

    raise HTTPException(status_code=404, detail="Post not found")


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: UUID):
    for post in posts:
        if post.id == post_id:
            posts.remove(post)
            return 

    raise HTTPException(status_code=404, detail="Post not found")

