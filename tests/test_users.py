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


def login(client: TestClient, user: dict[str, str]) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": user["email"], "password": user["password"]})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_delete_user_account(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    response = client.request("DELETE", "/api/users/me", json={"password": user_data["password"]})

    assert response.status_code == 204


def test_delete_user_account_rejects_wrong_password(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    response = client.request("DELETE", "/api/users/me", json={"password": "wrong-password"})

    assert response.status_code == 403
    assert client.post("/api/auth/login", json={"email": user_data["email"], "password": user_data["password"]}).status_code == 200


def test_delete_user_account_removes_posts(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    client.post("/api/posts", json=POST)

    client.request("DELETE", "/api/users/me", json={"password": user_data["password"]})

    with engine.connect() as connection:
        post_count = connection.execute(text("SELECT count(*) FROM posts")).scalar()
    assert post_count == 0


def test_deleted_user_token_is_rejected(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    client.request("DELETE", "/api/users/me", json={"password": user_data["password"]})

    response = client.get("/api/posts")

    assert response.status_code == 401


def test_delete_user_account_keeps_other_users_posts(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    client.post("/api/auth/signup", json=OTHER_USER)
    other_headers = login(client, OTHER_USER)
    client.post("/api/posts", json=POST, headers=other_headers)

    client.request("DELETE", "/api/users/me", json={"password": user_data["password"]})

    response = client.get("/api/posts", headers=other_headers)
    assert len(response.json()) == 1
