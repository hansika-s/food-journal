import pytest
from fastapi.testclient import TestClient

from app.services import places

GOOGLE_PLACE = {
    "id": "ChIJ-golden",
    "displayName": {"text": "Golden Spoon Germany"},
    "formattedAddress": "Rohrbacher Str. 65, 69115 Heidelberg, Germany",
    "addressComponents": [
        {"longText": "Heidelberg", "types": ["locality"]},
    ],
    "types": ["indian_restaurant", "restaurant"],
}
GOOGLE_SUGGESTIONS = {
    "suggestions": [
        {
            "placePrediction": {
                "placeId": "ChIJ-golden",
                "structuredFormat": {
                    "mainText": {"text": "Golden Spoon"},
                    "secondaryText": {"text": "Rohrbacher Str. 65, Heidelberg"},
                },
            }
        },
        {"queryPrediction": {"text": {"text": "golden spoon near me"}}},
    ]
}


def test_parse_place_maps_google_fields_to_ours() -> None:
    result = places.parse_place(GOOGLE_PLACE)

    assert result.place_id == "ChIJ-golden"
    assert result.name == "Golden Spoon Germany"
    assert result.city == "Heidelberg"
    assert result.types == ["indian_restaurant", "restaurant"]


def test_parse_places_handles_no_results() -> None:
    assert places.parse_places({}) == []


@pytest.fixture
def fake_google(monkeypatch):
    """Replaces the Google calls with fixed answers, so the tests use no quota."""

    def fake_autocomplete(query, session, location):
        return places.parse_suggestions(GOOGLE_SUGGESTIONS)

    def fake_details(place_id, session):
        return places.parse_place(GOOGLE_PLACE)

    monkeypatch.setattr(places, "autocomplete", fake_autocomplete)
    monkeypatch.setattr(places, "place_details", fake_details)


def test_autocomplete_returns_place_suggestions_only(client: TestClient, logged_in, fake_google) -> None:
    response = client.get("/api/places/autocomplete", params={"q": "golden sp"})

    assert response.status_code == 200
    assert response.json() == [
        {"place_id": "ChIJ-golden", "name": "Golden Spoon", "address": "Rohrbacher Str. 65, Heidelberg"}
    ]


def test_autocomplete_needs_at_least_two_letters(client: TestClient, logged_in) -> None:
    assert client.get("/api/places/autocomplete", params={"q": "g"}).status_code == 422


def test_details_returns_city_and_types(client: TestClient, logged_in, fake_google) -> None:
    response = client.get("/api/places/details/ChIJ-golden")

    assert response.status_code == 200
    assert response.json()["city"] == "Heidelberg"
    assert response.json()["types"] == ["indian_restaurant", "restaurant"]


def test_places_need_a_logged_in_user(client: TestClient) -> None:
    assert client.get("/api/places/autocomplete", params={"q": "golden"}).status_code == 401
    assert client.get("/api/places/details/ChIJ-golden").status_code == 401


def test_autocomplete_reports_when_google_fails(client: TestClient, logged_in, monkeypatch) -> None:
    def failing(query, session, location):
        raise places.PlaceSearchError("Restaurant search failed (403)")

    monkeypatch.setattr(places, "autocomplete", failing)

    response = client.get("/api/places/autocomplete", params={"q": "golden"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Restaurant search failed (403)"


def test_nearby_returns_restaurants_around_the_user(client: TestClient, logged_in, monkeypatch) -> None:
    monkeypatch.setattr(places, "nearby_places", lambda lat, lng: [places.parse_place(GOOGLE_PLACE)])

    response = client.get("/api/places/nearby", params={"lat": 49.4, "lng": 8.7})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Golden Spoon Germany"


def test_nearby_rejects_coordinates_out_of_range(client: TestClient, logged_in) -> None:
    assert client.get("/api/places/nearby", params={"lat": 120, "lng": 0}).status_code == 422
