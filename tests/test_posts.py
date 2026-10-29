import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.database import Base, engine
from app.main import app


client = TestClient(app)

USER = {"email": "post-tester@example.com", "password": "password123", "name": "Post Tester"}
OTHER_USER = {"email": "other-tester@example.com", "password": "password123", "name": "Other Tester"}


# Runs once per test session. Creates the tables, and drops them after all tests finish.
@pytest.fixture(scope="session", autouse=True)
def create_tables() -> Iterator[None]:
    # Safety check: refuse to run against a database that isn't a test database.
    if not (make_url(os.environ["DATABASE_URL"]).database or "").endswith("_test"):
        raise RuntimeError("DATABASE_URL must point at a database whose name ends in _test")
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


# Runs before every test. Empties the posts and users tables so each test starts with no data.
@pytest.fixture(autouse=True)
def clear_posts() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE posts, users"))


# Runs after clear_posts. Signs up and logs in a test user, and sends their token with every request.
@pytest.fixture(autouse=True)
def logged_in(clear_posts: None) -> Iterator[None]:
    client.post("/signup", json=USER)
    response = client.post("/login", json={"email": USER["email"], "password": USER["password"]})
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    yield
    client.headers.pop("Authorization", None)


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

    assert response.status_code == 201
    assert body["restaurant_name"] == "Ramen Nagi"
    assert body["rating"] == 5
    assert "id" in body
    assert "created_at" in body


def test_list_posts() -> None:
    create_response = create_test_post()

    list_response = client.get("/posts")

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert create_response.json() in list_response.json()


def test_list_newest_posts() -> None:
    first_post_id = create_test_post().json()["id"]
    second_post_id = create_test_post().json()["id"]

    list_response = client.get("/posts")

    assert list_response.json()[0]["id"] == second_post_id
    assert list_response.json()[1]["id"] == first_post_id


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


# Validation tests
def test_create_post_rejects_invalid_rating() -> None:
    response = client.post(
        "/posts",
        json={
            "restaurant_name": "Ramen Nagi",
            "city": "Berlin",
            "cuisine": "Japanese",
            "rating": 6,
            "tags": ["ramen"],
            "notes": "Great broth.",
        },
    )

    assert response.status_code == 422


def test_create_post_rejects_empty_restaurant_field() -> None:
    response = client.post(
        "/posts",
        json={
            "restaurant_name": "",
            "city": "Berlin",
            "cuisine": "Japanese",
            "rating": 5,
            "tags": ["ramen"],
            "notes": "Great broth.",
        },
    )

    assert response.status_code == 422


def test_update_post_rejects_invalid_rating() -> None:
    create_response = create_test_post()
    post_id = create_response.json()["id"]

    update_response = client.patch(
        f"/posts/{post_id}",
        json={
            "rating": 6,
        },
    )

    assert update_response.status_code == 422


def test_users_cannot_access_each_others_posts() -> None:
    owner_post = create_test_post().json()

    client.post("/signup", json=OTHER_USER)
    login = client.post("/login", json={"email": OTHER_USER["email"], "password": OTHER_USER["password"]})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    post_url = f"/posts/{owner_post['id']}"
    assert client.get(post_url).status_code == 404
    assert client.patch(post_url, json={"city": "Paris"}).status_code == 404
    assert client.delete(post_url).status_code == 404
    assert client.get("/posts").json() == []
