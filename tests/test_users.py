from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine

OTHER_USER = {"email": "other@example.com", "password": "password123", "name": "Other"}
POST = {
    "restaurant_name": "Ramen Nagi",
    "city": "Berlin",
    "cuisine": "Japanese",
    "rating": 5,
    "items": ["ramen"],
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




def update_profile(client: TestClient, **changes):
    return client.patch("/api/users/me", json=changes)


def test_change_name_needs_no_password(client: TestClient, logged_in: None) -> None:
    response = update_profile(client, name="Renamed")

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_change_password_rejects_wrong_current_password(client: TestClient, logged_in: None) -> None:
    assert update_profile(client, new_password="a-new-password", current_password="wrong-password").status_code == 403


def test_change_password_needs_the_current_password(client: TestClient, logged_in: None) -> None:
    assert update_profile(client, new_password="a-new-password").status_code == 403


def test_new_password_works_and_the_old_one_does_not(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    assert update_profile(client, new_password="a-new-password", current_password=user_data["password"]).status_code == 200

    assert client.post("/api/auth/login", json={"email": user_data["email"], "password": "a-new-password"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": user_data["email"], "password": user_data["password"]}).status_code == 401


def test_new_password_must_be_at_least_8_characters(client: TestClient, logged_in: None, user_data: dict[str, str]) -> None:
    assert update_profile(client, new_password="short", current_password=user_data["password"]).status_code == 422
