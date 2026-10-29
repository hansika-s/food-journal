import os
from collections.abc import Iterator

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.database import Base, SessionLocal, engine
from app.main import app, get_current_user


client = TestClient(app)

USER = {"email": "ana@example.com", "password": "password123", "name": "Ana"}
OTHER_USER = {"email": "other@example.com", "password": "password123", "name": "Other"}
POST = {
    "restaurant_name": "Ramen Nagi",
    "city": "Berlin",
    "cuisine": "Japanese",
    "rating": 5,
    "tags": ["ramen"],
    "notes": "Great broth.",
}


@pytest.fixture(scope="session", autouse=True)
def create_tables() -> Iterator[None]:
    if not (make_url(os.environ["DATABASE_URL"]).database or "").endswith("_test"):
        raise RuntimeError("DATABASE_URL must point at a database whose name ends in _test")
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clear_users() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE posts, users"))


# Signs up and logs in the test user, and sends their token with every request.
@pytest.fixture
def logged_in() -> Iterator[None]:
    client.post("/signup", json=USER)
    response = client.post("/login", json={"email": USER["email"], "password": USER["password"]})
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    yield
    client.headers.pop("Authorization", None)


def test_signup_creates_user() -> None:
    response = client.post("/signup", json={**USER, "email": "ANA@Example.com"})

    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    assert "password_hash" not in response.json()


def test_signup_rejects_duplicate_email() -> None:
    client.post("/signup", json=USER)

    response = client.post("/signup", json=USER)

    assert response.status_code == 409


def test_login_returns_token() -> None:
    client.post("/signup", json=USER)

    response = client.post("/login", json={"email": USER["email"], "password": USER["password"]})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_wrong_password() -> None:
    client.post("/signup", json=USER)

    response = client.post("/login", json={"email": USER["email"], "password": "wrong-password"})

    assert response.status_code == 401


def test_get_current_user_rejects_invalid_token() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token")

    with SessionLocal() as db:
        with pytest.raises(HTTPException) as error:
            get_current_user(credentials, db)

    assert error.value.status_code == 401


def test_delete_current_user(logged_in: None) -> None:
    response = client.request("DELETE", "/users/me", json={"password": USER["password"]})

    assert response.status_code == 204


def test_delete_current_user_rejects_wrong_password(logged_in: None) -> None:
    response = client.request("DELETE", "/users/me", json={"password": "wrong-password"})

    assert response.status_code == 403
    assert client.post("/login", json={"email": USER["email"], "password": USER["password"]}).status_code == 200


def test_delete_current_user_removes_posts(logged_in: None) -> None:
    client.post("/posts", json=POST)

    client.request("DELETE", "/users/me", json={"password": USER["password"]})

    with engine.connect() as connection:
        post_count = connection.execute(text("SELECT count(*) FROM posts")).scalar()
    assert post_count == 0


def test_delete_current_user_rejects_old_token(logged_in: None) -> None:
    client.request("DELETE", "/users/me", json={"password": USER["password"]})

    response = client.get("/posts")

    assert response.status_code == 401


def test_delete_current_user_keeps_other_users_posts(logged_in: None) -> None:
    client.post("/signup", json=OTHER_USER)
    other_login = client.post("/login", json={"email": OTHER_USER["email"], "password": OTHER_USER["password"]})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    client.post("/posts", json=POST, headers=other_headers)

    client.request("DELETE", "/users/me", json={"password": USER["password"]})

    response = client.get("/posts", headers=other_headers)
    assert len(response.json()) == 1
