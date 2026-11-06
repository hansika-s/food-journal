import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.dependencies import get_current_user

USER = {"email": "ana@example.com", "password": "password123", "name": "Ana"}


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
