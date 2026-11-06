from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.database import SessionLocal
from app.dependencies import get_current_user
from app.models import RefreshToken

USER = {"email": "ana@example.com", "password": "password123", "name": "Ana"}


def sign_up_and_log_in(client: TestClient) -> dict[str, str]:
    client.post("/api/auth/signup", json=USER)
    response = client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})
    return response.json()


def test_signup_creates_user(client: TestClient) -> None:
    response = client.post("/api/auth/signup", json={**USER, "email": "ANA@Example.com"})

    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    assert "password_hash" not in response.json()


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)

    response = client.post("/api/auth/signup", json=USER)

    assert response.status_code == 409


def test_login_returns_token(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)

    response = client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["refresh_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    client.post("/api/auth/signup", json=USER)

    response = client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong-password"})

    assert response.status_code == 401


def test_get_current_user_rejects_invalid_token() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token")

    with SessionLocal() as db:
        with pytest.raises(HTTPException) as error:
            get_current_user(credentials, db)

    assert error.value.status_code == 401


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

    logout_response = client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert logout_response.status_code == 204
    assert refresh_response.status_code == 401
