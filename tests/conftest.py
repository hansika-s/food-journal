import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.database import Base, engine
from app.main import app


# Runs once per test session. Creates the tables, and drops them after all tests finish.
@pytest.fixture(scope="session", autouse=True)
def create_tables() -> Iterator[None]:
    # Safety check: refuse to run against a database that isn't a test database.
    if not (make_url(os.environ["DATABASE_URL"]).database or "").endswith("_test"):
        raise RuntimeError("DATABASE_URL must point at a database whose name ends in _test")
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


# Runs before every test. Empties the tables so each test starts with no data.
@pytest.fixture(autouse=True)
def clear_database() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE posts, users, restaurants, refresh_tokens"))


# A new client for each test, so headers set in one test don't leak into the next.
@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def user_data() -> dict[str, str]:
    return {"email": "tester@example.com", "password": "password123", "name": "Tester"}


# Signs up and logs in the test user, and sends their token with every request made through client.
@pytest.fixture
def logged_in(client: TestClient, user_data: dict[str, str]) -> None:
    client.post("/api/auth/signup", json=user_data)
    response = client.post("/api/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
