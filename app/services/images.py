import uuid
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import MAX_IMAGES_PER_POST, UPLOAD_DIR
from app.models import Post, PostImage

EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


class ImageError(Exception):
    pass


# Works out the image type from the file's first bytes, not from its name or the type the client sent.
def detect_image_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def image_path(image: PostImage) -> Path:
    return UPLOAD_DIR / image.filename


# Stores the file and adds a row for it. Raises ImageError if the image isn't allowed.
def add_image(db: Session, post: Post, data: bytes) -> PostImage:
    if len(post.images) >= MAX_IMAGES_PER_POST:
        raise ImageError(f"A post can have at most {MAX_IMAGES_PER_POST} images")

    content_type = detect_image_type(data)
    if content_type is None:
        raise ImageError("Only JPEG, PNG and WebP images are allowed")

    image = PostImage(
        post_id=post.id,
        filename=f"{uuid.uuid4()}{EXTENSIONS[content_type]}",
        content_type=content_type,
    )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path(image).write_bytes(data)
    db.add(image)
    db.commit()
    db.refresh(post)
    return image


def delete_image(db: Session, image: PostImage) -> None:
    image_path(image).unlink(missing_ok=True)
    db.delete(image)
    db.commit()


# Removes the files for images that are about to be deleted along with their post or user.
def delete_image_files(images: list[PostImage]) -> None:
    for image in images:
        image_path(image).unlink(missing_ok=True)


def delete_image_files_for_user(db: Session, user_id: UUID) -> None:
    images = db.scalars(select(PostImage).join(Post).where(Post.user_id == user_id)).all()
    delete_image_files(list(images))
