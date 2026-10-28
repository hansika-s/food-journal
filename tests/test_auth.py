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
        connection.execute(text("TRUNCATE users"))


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
