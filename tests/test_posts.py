import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine

pytestmark = pytest.mark.usefixtures("logged_in")

POST_BODY = {
    "restaurant_name": "Ramen Nagi",
    "city": "Berlin",
    "cuisine": "Japanese",
    "rating": 5,
    "tags": ["ramen", "spicy"],
    "notes": "Great broth.",
}
OTHER_USER = {"email": "other-tester@example.com", "password": "password123", "name": "Other Tester"}
MISSING_ID = "00000000-0000-0000-0000-000000000000"


def create_test_post(client: TestClient):
    return client.post("/api/posts", json=POST_BODY)


def count_restaurants() -> int:
    with engine.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM restaurants")).scalar_one()


def log_in_as_other_user(client: TestClient) -> None:
    client.post("/api/auth/signup", json=OTHER_USER)
    login = client.post("/api/auth/login", json={"email": OTHER_USER["email"], "password": OTHER_USER["password"]})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"


def test_create_post(client: TestClient) -> None:
    response = create_test_post(client)

    assert response.status_code == 201
    assert response.json()["restaurant"]["name"] == "Ramen Nagi"


def test_create_post_rejects_invalid_rating(client: TestClient) -> None:
    assert client.post("/api/posts", json={**POST_BODY, "rating": 6}).status_code == 422


def test_create_post_rejects_empty_restaurant_name(client: TestClient) -> None:
    assert client.post("/api/posts", json={**POST_BODY, "restaurant_name": ""}).status_code == 422


def test_list_posts_newest_first(client: TestClient) -> None:
    first_id = create_test_post(client).json()["id"]
    second_id = client.post("/api/posts", json={**POST_BODY, "restaurant_name": "Sushi Bar"}).json()["id"]

    posts = client.get("/api/posts").json()

    assert [post["id"] for post in posts] == [second_id, first_id]


def test_list_posts_filters_by_city_ignoring_case(client: TestClient) -> None:
    create_test_post(client)

    assert len(client.get("/api/posts", params={"city": "berlin"}).json()) == 1
    assert client.get("/api/posts", params={"city": "Hamburg"}).json() == []


def test_list_posts_filters_by_cuisine_ignoring_case(client: TestClient) -> None:
    create_test_post(client)

    assert len(client.get("/api/posts", params={"cuisine": "japanese"}).json()) == 1
    assert client.get("/api/posts", params={"cuisine": "Italian"}).json() == []


def test_get_post_by_id(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    assert client.get(f"/api/posts/{post_id}").json()["id"] == post_id


def test_get_missing_post_returns_404(client: TestClient) -> None:
    assert client.get(f"/api/posts/{MISSING_ID}").status_code == 404


def test_update_post(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    response = client.patch(f"/api/posts/{post_id}", json={"rating": 4})

    assert response.status_code == 200
    assert response.json()["rating"] == 4
    assert response.json()["restaurant"]["name"] == "Ramen Nagi"


def test_update_post_rejects_invalid_rating(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    assert client.patch(f"/api/posts/{post_id}", json={"rating": 6}).status_code == 422


def test_update_missing_post_returns_404(client: TestClient) -> None:
    assert client.patch(f"/api/posts/{MISSING_ID}", json={"rating": 4}).status_code == 404


def test_delete_post(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    assert client.delete(f"/api/posts/{post_id}").status_code == 204
    assert client.get(f"/api/posts/{post_id}").status_code == 404


def test_delete_missing_post_returns_404(client: TestClient) -> None:
    assert client.delete(f"/api/posts/{MISSING_ID}").status_code == 404


def test_users_cannot_access_each_others_posts(client: TestClient) -> None:
    post_url = f"/api/posts/{create_test_post(client).json()['id']}"

    log_in_as_other_user(client)

    assert client.get(post_url).status_code == 404
    assert client.patch(post_url, json={"rating": 1}).status_code == 404
    assert client.delete(post_url).status_code == 404
    assert client.get("/api/posts").json() == []


def test_same_restaurant_is_shared(client: TestClient) -> None:
    first = create_test_post(client).json()
    second = client.post(
        "/api/posts", json={**POST_BODY, "restaurant_name": " ramen nagi ", "city": "berlin"}
    ).json()

    assert second["restaurant"] == first["restaurant"]
    assert count_restaurants() == 1


def test_same_name_in_another_city_is_a_separate_restaurant(client: TestClient) -> None:
    create_test_post(client)

    client.post("/api/posts", json={**POST_BODY, "city": "Hamburg"})

    assert count_restaurants() == 2
