import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import text

from app.config import MAX_IMAGE_BYTES
from app.database import engine
from app.services import images

pytestmark = pytest.mark.usefixtures("logged_in")

POST_BODY = {
    "restaurant_name": "Ramen Nagi",
    "city": "Berlin",
    "cuisine": "Japanese",
    "rating": 5,
    "items": ["ramen", "gyoza"],
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


def test_rating_accepts_one_decimal_place(client: TestClient) -> None:
    response = client.post("/api/posts", json={**POST_BODY, "rating": 4.5})

    assert response.status_code == 201
    assert response.json()["rating"] == 4.5


def test_rating_rejects_two_decimal_places(client: TestClient) -> None:
    assert client.post("/api/posts", json={**POST_BODY, "rating": 4.25}).status_code == 422


def test_update_rating_accepts_one_decimal_place(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    assert client.patch(f"/api/posts/{post_id}", json={"rating": 3.5}).json()["rating"] == 3.5
    assert client.patch(f"/api/posts/{post_id}", json={"rating": 3.25}).status_code == 422


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


def test_update_can_change_the_restaurant(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    response = client.patch(f"/api/posts/{post_id}", json={"restaurant_name": "Sushi Bar", "city": "Hamburg"})

    assert response.status_code == 200
    assert response.json()["restaurant"]["name"] == "Sushi Bar"
    assert response.json()["restaurant"]["city"] == "Hamburg"
    assert response.json()["restaurant"]["cuisine"] == "Japanese"


def test_changing_the_restaurant_leaves_other_posts_alone(client: TestClient) -> None:
    first_id = create_test_post(client).json()["id"]
    second_id = create_test_post(client).json()["id"]

    client.patch(f"/api/posts/{first_id}", json={"restaurant_name": "Sushi Bar"})

    assert client.get(f"/api/posts/{second_id}").json()["restaurant"]["name"] == "Ramen Nagi"


def test_update_rejects_an_empty_restaurant_name(client: TestClient) -> None:
    post_id = create_test_post(client).json()["id"]

    assert client.patch(f"/api/posts/{post_id}", json={"restaurant_name": ""}).status_code == 422


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


def make_image(image_format: str = "JPEG", size: tuple[int, int] = (20, 20), exif: Image.Exif | None = None) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, "orange").save(output, format=image_format, **({"exif": exif} if exif else {}))
    return output.getvalue()


PNG = make_image("PNG")


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(images, "UPLOAD_DIR", tmp_path)
    return tmp_path


def upload_image(client: TestClient, post_id: str, data: bytes = PNG):
    return client.post(f"/api/posts/{post_id}/images", files={"file": ("photo.png", data, "image/png")})


def test_upload_image_and_fetch_it(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]

    response = upload_image(client, post_id)
    image_id = response.json()["images"][0]["id"]
    fetched = client.get(f"/api/posts/{post_id}/images/{image_id}")

    assert response.status_code == 201
    assert fetched.headers["content-type"] == "image/webp"
    assert Image.open(io.BytesIO(fetched.content)).format == "WEBP"


def test_upload_accepts_an_iphone_heic_photo(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]

    response = upload_image(client, post_id, data=make_image("HEIF"))

    assert response.status_code == 201
    stored = next(upload_dir.iterdir())
    assert Image.open(stored).format == "WEBP"


def test_upload_removes_the_gps_location(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]
    exif = Image.Exif()
    gps = exif.get_ifd(0x8825)
    gps[1] = "N"
    exif[0x8825] = gps

    upload_image(client, post_id, data=make_image("JPEG", exif=exif))

    stored = next(upload_dir.iterdir())
    assert 0x8825 not in Image.open(stored).getexif()


def test_upload_rotates_the_image_upright(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]
    exif = Image.Exif()
    exif[0x0112] = 6  # Stored sideways; the phone rotates it 90 degrees when shown.

    upload_image(client, post_id, data=make_image("JPEG", size=(40, 20), exif=exif))

    stored = next(upload_dir.iterdir())
    assert Image.open(stored).size == (20, 40)


def test_upload_shrinks_large_images(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]

    upload_image(client, post_id, data=make_image("JPEG", size=(3000, 2000)))

    stored = next(upload_dir.iterdir())
    assert max(Image.open(stored).size) == 1600


def test_upload_rejects_a_file_that_is_not_an_image(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]

    assert upload_image(client, post_id, data=b"not an image").status_code == 422


def test_upload_rejects_a_file_with_an_image_header_but_no_image(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]

    assert upload_image(client, post_id, data=b"\x89PNG\r\n\x1a\n" + b"0" * 100).status_code == 422


def test_upload_rejects_an_image_over_5_mb(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]

    assert upload_image(client, post_id, data=PNG + b"0" * MAX_IMAGE_BYTES).status_code == 413


def test_a_post_takes_at_most_5_images(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]
    for _ in range(5):
        upload_image(client, post_id)

    assert upload_image(client, post_id).status_code == 422


def test_other_users_cannot_see_or_upload_images(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]
    image_id = upload_image(client, post_id).json()["images"][0]["id"]

    log_in_as_other_user(client)

    assert client.get(f"/api/posts/{post_id}/images/{image_id}").status_code == 404
    assert upload_image(client, post_id).status_code == 404


def test_delete_image_removes_it_and_its_file(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]
    image_id = upload_image(client, post_id).json()["images"][0]["id"]

    assert client.delete(f"/api/posts/{post_id}/images/{image_id}").status_code == 204
    assert list(upload_dir.iterdir()) == []


def test_deleting_a_post_removes_its_image_files(client: TestClient, upload_dir) -> None:
    post_id = create_test_post(client).json()["id"]
    upload_image(client, post_id)

    client.delete(f"/api/posts/{post_id}")

    assert list(upload_dir.iterdir()) == []
