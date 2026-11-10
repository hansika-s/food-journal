import re
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.database import SessionLocal
from app.models import RefreshToken

USER = {"email": "ana@example.com", "password": "password123", "name": "Ana"}
POST_BODY = {"restaurant_name": "Ramen Nagi", "city": "Berlin", "cuisine": "Japanese", "rating": 5}


def sign_up_and_log_in(client: TestClient) -> dict[str, str]:
    client.post("/api/auth/signup", json=USER)
    response = client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})
    return response.json()


def log_in_with_form(client: TestClient) -> None:
    client.post("/login", data={"email": USER["email"], "password": USER["password"]})


def csrf_token(client: TestClient) -> str:
    match = re.search(r'name="csrf-token" content="([^"]+)"', client.get("/posts").text)
    assert match is not None
    return match.group(1)


def test_signup_creates_user(client: TestClient) -> None:
    response = client.post("/api/auth/signup", json=USER)

    assert response.status_code == 201
    assert "password_hash" not in response.json()


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)

    assert client.post("/api/auth/signup", json=USER).status_code == 409


def test_login_returns_tokens(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)

    response = client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)

    response = client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong-password"})

    assert response.status_code == 401


def test_invalid_access_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/users/me", headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401


def test_refresh_rotates_tokens(client: TestClient) -> None:
    tokens = sign_up_and_log_in(client)

    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    old_token_response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["refresh_token"] != tokens["refresh_token"]
    assert old_token_response.status_code == 401


def test_reusing_a_refresh_token_revokes_all_tokens(client: TestClient) -> None:
    tokens = sign_up_and_log_in(client)
    new_tokens = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
    client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    response = client.post("/api/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})

    assert response.status_code == 401


def test_expired_refresh_token_is_rejected(client: TestClient) -> None:
    tokens = sign_up_and_log_in(client)
    with SessionLocal() as db:
        db.execute(update(RefreshToken).values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        db.commit()

    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401


def test_logout_revokes_the_refresh_token(client: TestClient) -> None:
    tokens = sign_up_and_log_in(client)

    client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert refresh_response.status_code == 401


def test_browser_write_needs_csrf_token(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)
    log_in_with_form(client)

    assert client.post("/api/posts", json=POST_BODY).status_code == 403
    assert client.post("/api/posts", json=POST_BODY, headers={"X-CSRF-Token": csrf_token(client)}).status_code == 201


def test_logout_ends_browser_session(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)
    log_in_with_form(client)

    client.post("/logout", data={"csrf_token": csrf_token(client)})

    assert client.get("/api/posts").status_code == 401


def test_posts_page_redirects_when_logged_out(client: TestClient) -> None:
    response = client.get("/posts", follow_redirects=False)

    assert response.headers["location"] == "/login"
