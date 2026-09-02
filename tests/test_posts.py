import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app, posts


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_posts() -> None:
    posts.clear()


def create_test_post() -> Response:
    return client.post(
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


def test_create_post() -> None:
    response = create_test_post()
    body = response.json()

    assert response.status_code == 200
    assert body["restaurant_name"] == "Ramen Nagi"
    assert body["rating"] == 5
    assert "id" in body
    assert "created_at" in body


def test_list_posts() -> None:
    create_response = create_test_post()

    list_response = client.get("/posts")

    assert create_response.status_code == 200
    assert list_response.status_code == 200
    assert create_response.json() in list_response.json()


def test_get_post_by_id() -> None:
    create_response = create_test_post()

    post_id = create_response.json()["id"]
    response = client.get(f"/posts/{post_id}")

    assert response.status_code == 200
    assert response.json() == create_response.json()


def test_get_missing_post_returns_404() -> None:
    response = client.get("/posts/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_update_post() -> None:
    create_response = create_test_post()
    post_id = create_response.json()["id"]

    update_response = client.patch(
        f"/posts/{post_id}",
        json={
            "rating": 4,
            "notes": "Still good, but not perfect.",
        },
    )

    body = update_response.json()

    assert update_response.status_code == 200
    assert body["rating"] == 4
    assert body["notes"] == "Still good, but not perfect."

    assert body["restaurant_name"] == "Ramen Nagi"
    assert body["city"] == "Berlin"
    assert body["cuisine"] == "Japanese"


def test_update_missing_post_returns_404() -> None:
    response = client.patch(
        "/posts/00000000-0000-0000-0000-000000000000",
        json={"rating": 4},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_delete_post() -> None:
    create_response = create_test_post()
    post_id = create_response.json()["id"]

    delete_response = client.delete(f"/posts/{post_id}")

    get_response = client.get(f"/posts/{post_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_missing_post_returns_404() -> None:
    response = client.delete(
        "/posts/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}