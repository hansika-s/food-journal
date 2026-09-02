from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
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


@app.post("/posts")
def create_post(post: PostCreate) -> PostResponse:
    new_post = PostResponse(
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
        **post.model_dump(),
    )
    posts.append(new_post)
    return new_post


@app.get("/posts")
def list_posts() -> list[PostResponse]:
    return posts


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

