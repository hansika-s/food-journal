from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine

OTHER_USER = {"email": "other@example.com", "password": "password123", "name": "Other"}
POST = {
    "restaurant_name": "Ramen Nagi",
    "city": "Berlin",
    "cuisine": "Japanese",
    "rating": 5,
    "tags": ["ramen"],
    "notes": "Great broth.",
}


def count_posts() -> int:
    with engine.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM posts")).scalar_one()


def test_get_user_profile(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    response = client.get("/api/users/me")

    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    assert "password_hash" not in response.json()


def test_get_user_profile_requires_token(client: TestClient) -> None:
    assert client.get("/api/users/me").status_code == 401


def test_delete_user_account_rejects_wrong_password(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    response = client.request("DELETE", "/api/users/me", json={"password": "wrong-password"})

    assert response.status_code == 403
    assert client.post("/api/auth/login", json={"email": user_data["email"], "password": user_data["password"]}).status_code == 200


def test_delete_user_account_removes_posts(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    client.post("/api/posts", json=POST)

    assert client.request("DELETE", "/api/users/me", json={"password": user_data["password"]}).status_code == 204
    assert count_posts() == 0


def test_deleted_user_token_is_rejected(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    client.request("DELETE", "/api/users/me", json={"password": user_data["password"]})

    assert client.get("/api/posts").status_code == 401


def test_delete_user_account_keeps_other_users_posts(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    client.post("/api/auth/signup", json=OTHER_USER)
    login = client.post("/api/auth/login", json={"email": OTHER_USER["email"], "password": OTHER_USER["password"]})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    client.post("/api/posts", json=POST, headers=other_headers)

    client.request("DELETE", "/api/users/me", json={"password": user_data["password"]})

    assert len(client.get("/api/posts", headers=other_headers).json()) == 1
