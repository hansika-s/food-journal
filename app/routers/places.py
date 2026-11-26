from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.dependencies import get_current_user
from app.models import User
from app.schemas.places import PlaceResult, Suggestion
from app.services import places

router = APIRouter(
    prefix="/api/places",
    tags=["Places"])


def _fail(error: places.PlaceSearchError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


@router.get("/autocomplete")
def autocomplete(
    q: str = Query(min_length=2, max_length=100),
    session: str | None = Query(default=None, max_length=100),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    current_user: User = Depends(get_current_user),
) -> list[Suggestion]:
    location = (lat, lng) if lat is not None and lng is not None else None
    try:
        return places.autocomplete(q.strip(), session, location)
    except places.PlaceSearchError as error:
        raise _fail(error)


@router.get("/details/{place_id}")
def details(
    place_id: str = Path(max_length=200),
    session: str | None = Query(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
) -> PlaceResult:
    try:
        return places.place_details(place_id, session)
    except places.PlaceSearchError as error:
        raise _fail(error)


@router.get("/nearby")
def nearby(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    current_user: User = Depends(get_current_user),
) -> list[PlaceResult]:
    try:
        return places.nearby_places(lat, lng)
    except places.PlaceSearchError as error:
        raise _fail(error)
