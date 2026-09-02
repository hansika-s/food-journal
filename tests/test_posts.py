from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_post() -> None:
    response = client.post(
        "/posts",
        json={
            "restaurant_name": "Ramen Nagi",
            "city": "Berlin",
            "cuisine": "Japanese",
            "rating": 5,
            "tags": ["ramen", "spicy"],
            "notes": "Great broth.",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["restaurant_name"] == "Ramen Nagi"
    assert body["rating"] == 5
    assert "id" in body
    assert "created_at" in body