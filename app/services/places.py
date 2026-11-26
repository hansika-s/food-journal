import httpx

from app.config import GOOGLE_PLACES_API_KEY
from app.schemas.places import PlaceResult, Suggestion

AUTOCOMPLETE_URL = "https://places.googleapis.com/v1/places:autocomplete"
NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
DETAILS_FIELDS = "id,displayName,formattedAddress,addressComponents,types"
NEARBY_FIELDS = "places.id,places.displayName,places.formattedAddress,places.addressComponents,places.types"
# Food and drink places only, so offices and hotels don't show up.
# Google accepts at most 5 types per search.
FOOD_PLACE_TYPES = ["restaurant", "cafe", "coffee_shop", "bar", "bakery"]
# Ranking distances: suggestions prefer places within this distance; the nearby list covers this distance.
BIAS_RADIUS_METERS = 5000.0
NEARBY_RADIUS_METERS = 2000.0


class PlaceSearchError(Exception):
    pass


def _city(place: dict) -> str | None:
    return next(
        (part["longText"] for part in place.get("addressComponents", []) if "locality" in part.get("types", [])),
        None,
    )


# Turns Google's place into our shape. Kept separate so it can be tested without calling Google.
def parse_place(place: dict) -> PlaceResult:
    return PlaceResult(
        place_id=place["id"],
        name=place.get("displayName", {}).get("text", ""),
        address=place.get("formattedAddress", ""),
        city=_city(place),
        types=place.get("types", []),
    )


def parse_places(data: dict) -> list[PlaceResult]:
    return [parse_place(place) for place in data.get("places", [])]


def _circle(lat: float, lng: float, radius: float) -> dict:
    return {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius}}


# Sends one request to Google and returns its JSON. Every failure becomes a PlaceSearchError.
def _send(method: str, url: str, *, body: dict | None = None, field_mask: str | None = None, params: dict | None = None) -> dict:
    if not GOOGLE_PLACES_API_KEY:
        raise PlaceSearchError("Restaurant search is not set up on the server")
    headers = {"X-Goog-Api-Key": GOOGLE_PLACES_API_KEY}
    if field_mask:
        headers["X-Goog-FieldMask"] = field_mask
    try:
        response = httpx.request(method, url, json=body, params=params, headers=headers, timeout=10)
    except httpx.HTTPError as error:
        raise PlaceSearchError("Restaurant search is unavailable right now") from error
    if response.status_code != 200:
        raise PlaceSearchError(f"Restaurant search failed ({response.status_code})")
    return response.json()


# Suggestions for what the user has typed so far. Built for partial words, so "golden sp" works.
def autocomplete(query: str, session: str | None, location: tuple[float, float] | None) -> list[Suggestion]:
    body: dict = {"input": query, "includedPrimaryTypes": FOOD_PLACE_TYPES}
    if session:
        body["sessionToken"] = session
    if location is not None:
        body["locationBias"] = _circle(location[0], location[1], BIAS_RADIUS_METERS)

    return parse_suggestions(_send("POST", AUTOCOMPLETE_URL, body=body))


# Turns Google's suggestion answer into our shape. Kept separate so it can be tested without calling Google.
def parse_suggestions(data: dict) -> list[Suggestion]:
    suggestions = []
    for item in data.get("suggestions", []):
        prediction = item.get("placePrediction")
        if not prediction:
            continue
        structured = prediction.get("structuredFormat", {})
        suggestions.append(
            Suggestion(
                place_id=prediction["placeId"],
                name=structured.get("mainText", {}).get("text") or prediction.get("text", {}).get("text", ""),
                address=structured.get("secondaryText", {}).get("text", ""),
            )
        )
    return suggestions


# Full details of one place, picked from the suggestions. Gives the city and types we need.
def place_details(place_id: str, session: str | None) -> PlaceResult:
    params = {"sessionToken": session} if session else None
    data = _send("GET", DETAILS_URL.format(place_id=place_id), field_mask=DETAILS_FIELDS, params=params)
    return parse_place(data)


# Lists food and drink places around a location, for when the user hasn't typed anything yet.
def nearby_places(lat: float, lng: float) -> list[PlaceResult]:
    body = {
        "includedTypes": FOOD_PLACE_TYPES,
        "maxResultCount": 10,
        "locationRestriction": _circle(lat, lng, NEARBY_RADIUS_METERS),
    }
    return parse_places(_send("POST", NEARBY_URL, body=body, field_mask=NEARBY_FIELDS))
