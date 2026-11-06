import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import text

from app.database import engine

pytestmark = pytest.mark.usefixtures("logged_in")

OTHER_USER = {"email": "other-tester@example.com", "password": "password123", "name": "Other Tester"}


def create_test_post(client: TestClient) -> Response:
    return client.post(
        "/api/posts",
        json={
            "restaurant_name": "Ramen Nagi",
            "city": "Berlin",
            "cuisine": "Japanese",
            "rating": 5,
            "tags": ["ramen", "spicy"],
            "notes": "Great broth.",
        },
    )


def test_create_post(client: TestClient) -> None:
    response = create_test_post(client)
    body = response.json()

    assert response.status_code == 201
    assert body["restaurant"]["name"] == "Ramen Nagi"
    assert body["rating"] == 5
    assert "id" in body
    assert "created_at" in body


def test_list_posts(client: TestClient) -> None:
    create_response = create_test_post(client)

    list_response = client.get("/api/posts")

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert create_response.json() in list_response.json()


def test_list_newest_posts(client: TestClient) -> None:
    first_post_id = create_test_post(client).json()["id"]
    second_post_id = create_test_post(client).json()["id"]

    list_response = client.get("/api/posts")

    assert list_response.json()[0]["id"] == second_post_id
    assert list_response.json()[1]["id"] == first_post_id


def test_list_posts_filters_by_city_ignoring_case(client: TestClient) -> None:
    create_test_post(client)

    assert len(client.get("/api/posts", params={"city": "berlin"}).json()) == 1
    assert client.get("/api/posts", params={"city": "Hamburg"}).json() == []


def test_list_posts_filters_by_cuisine_ignoring_case(client: TestClient) -> None:
    create_test_post(client)

    assert len(client.get("/api/posts", params={"cuisine": "japanese"}).json()) == 1
    assert client.get("/api/posts", params={"cuisine": "Italian"}).json() == []


def test_get_post_by_id(client: TestClient) -> None:
    create_response = create_test_post(client)

    post_id = create_response.json()["id"]
    response = client.get(f"/api/posts/{post_id}")

    assert response.status_code == 200
    assert response.json() == create_response.json()


def test_get_missing_post_returns_404(client: TestClient) -> None:
    response = client.get("/api/posts/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_update_post(client: TestClient) -> None:
    create_response = create_test_post(client)
    post_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/posts/{post_id}",
        json={
            "rating": 4,
            "notes": "Still good, but not perfect.",
        },
    )

    body = update_response.json()

    assert update_response.status_code == 200
    assert body["rating"] == 4
    assert body["notes"] == "Still good, but not perfect."

    assert body["restaurant"] == {"name": "Ramen Nagi", "city": "Berlin", "cuisine": "Japanese"}


def test_update_missing_post_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/posts/00000000-0000-0000-0000-000000000000",
        json={"rating": 4},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_delete_post(client: TestClient) -> None:
    create_response = create_test_post(client)
    post_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/posts/{post_id}")

    get_response = client.get(f"/api/posts/{post_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_missing_post_returns_404(client: TestClient) -> None:
    response = client.delete(
        "/api/posts/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


# Validation tests
def test_create_post_rejects_invalid_rating(client: TestClient) -> None:
    response = client.post(
        "/api/posts",
        json={
            "restaurant_name": "Ramen Nagi",
            "city": "Berlin",
            "cuisine": "Japanese",
            "rating": 6,
            "tags": ["ramen"],
            "notes": "Great broth.",
        },
    )

    assert response.status_code == 422


def test_create_post_rejects_empty_restaurant_field(client: TestClient) -> None:
    response = client.post(
        "/api/posts",
        json={
            "restaurant_name": "",
            "city": "Berlin",
            "cuisine": "Japanese",
            "rating": 5,
            "tags": ["ramen"],
            "notes": "Great broth.",
        },
    )

    assert response.status_code == 422


def test_update_post_rejects_invalid_rating(client: TestClient) -> None:
    create_response = create_test_post(client)
    post_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/posts/{post_id}",
        json={
            "rating": 6,
        },
    )

    assert update_response.status_code == 422


def test_users_cannot_access_each_others_posts(client: TestClient) -> None:
    owner_post = create_test_post(client).json()

    client.post("/api/auth/signup", json=OTHER_USER)
    login = client.post("/api/auth/login", json={"email": OTHER_USER["email"], "password": OTHER_USER["password"]})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    post_url = f"/api/posts/{owner_post['id']}"
    assert client.get(post_url).status_code == 404
    assert client.patch(post_url, json={"rating": 1}).status_code == 404
    assert client.delete(post_url).status_code == 404
    assert client.get("/api/posts").json() == []


def count_restaurants() -> int:
    with engine.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM restaurants")).scalar()


def test_same_restaurant_is_shared_and_keeps_first_cuisine(client: TestClient) -> None:
    first = create_test_post(client).json()
    second = client.post(
        "/api/posts",
        json={"restaurant_name": " ramen nagi ", "city": "berlin", "cuisine": "Ramen", "rating": 4},
    ).json()

    assert second["restaurant"] == first["restaurant"]
    assert second["restaurant"]["cuisine"] == "Japanese"
    assert count_restaurants() == 1


def test_same_name_in_another_city_is_a_separate_restaurant(client: TestClient) -> None:
    create_test_post(client)

    client.post(
        "/api/posts",
        json={"restaurant_name": "Ramen Nagi", "city": "Hamburg", "cuisine": "Japanese", "rating": 3},
    )

    assert count_restaurants() == 2
