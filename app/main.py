from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI
from pydantic import BaseModel


class PostCreate(BaseModel):
    restaurant_name: str
    city: str
    cuisine: str
    rating: int
    tags: list[str]
    notes: str


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
