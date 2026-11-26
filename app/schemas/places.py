from pydantic import BaseModel


class Suggestion(BaseModel):
    place_id: str
    name: str
    address: str


class PlaceResult(BaseModel):
    place_id: str
    name: str
    address: str
    city: str | None
    types: list[str]
