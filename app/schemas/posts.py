from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    restaurant_name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    cuisine: str = Field(min_length=1)
    rating: Decimal = Field(ge=1, le=5, max_digits=2, decimal_places=1)
    items: list[str] = Field(default_factory=list)
    notes: str = ""


class PostUpdate(BaseModel):
    rating: Decimal | None = Field(default=None, ge=1, le=5, max_digits=2, decimal_places=1)
    items: list[str] | None = None
    notes: str | None = None


class RestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    city: str
    cuisine: str


class PostImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant: RestaurantResponse
    rating: float
    items: list[str]
    notes: str
    images: list[PostImageResponse]
    created_at: datetime
