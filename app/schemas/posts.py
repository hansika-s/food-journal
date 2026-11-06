from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    restaurant_name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    cuisine: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    notes: str = ""


class PostUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] | None = None
    notes: str | None = None


class RestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    city: str
    cuisine: str


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant: RestaurantResponse
    rating: int
    tags: list[str]
    notes: str
    created_at: datetime
