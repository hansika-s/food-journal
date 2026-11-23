import io
import uuid
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import MAX_IMAGES_PER_POST, UPLOAD_DIR
from app.models import Post, PostImage

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_DIMENSION = 1600
WEBP_QUALITY = 80


class ImageError(Exception):
    pass


# Decodes the upload, rotates it upright, shrinks it and saves it as WebP.
# Saving only the pixels drops metadata such as the GPS location. Raises ImageError if the file isn't a supported image.
def process_image(data: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in ALLOWED_FORMATS:
                raise ImageError("Only JPEG, PNG and WebP images are allowed")
            image = ImageOps.exif_transpose(source)
            image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
            output = io.BytesIO()
            image.save(output, format="WEBP", quality=WEBP_QUALITY)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as error:
        raise ImageError("Only JPEG, PNG and WebP images are allowed") from error
    return output.getvalue()


def image_path(image: PostImage) -> Path:
    return UPLOAD_DIR / image.filename


# Stores the processed file and adds a row for it. Raises ImageError if the image isn't allowed.
def add_image(db: Session, post: Post, data: bytes) -> PostImage:
    if len(post.images) >= MAX_IMAGES_PER_POST:
        raise ImageError(f"A post can have at most {MAX_IMAGES_PER_POST} images")

    webp = process_image(data)
    image = PostImage(
        post_id=post.id,
        filename=f"{uuid.uuid4()}.webp",
        content_type="image/webp",
    )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path(image).write_bytes(webp)
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
