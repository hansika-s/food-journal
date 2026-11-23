from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config import MAX_IMAGE_BYTES
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Post, PostImage, Restaurant, User
from app.schemas.posts import PostCreate, PostResponse, PostUpdate
from app.services import images
from app.services.restaurants import get_or_create_restaurant

router = APIRouter(
    prefix="/api/posts",
    tags=["Posts"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    restaurant = get_or_create_restaurant(db, post.restaurant_name, post.city, post.cuisine)
    new_post = Post(
        user_id=current_user.id,
        restaurant=restaurant,
        rating=post.rating,
        tags=post.tags,
        notes=post.notes,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return PostResponse.model_validate(new_post)


@router.get("")
def list_posts(
    city: str | None = None,
    cuisine: str | None = None,
    min_rating: int | None = Query(default=None, ge=1, le=5),
    tag: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PostResponse]:
    statement = select(Post).join(Post.restaurant).where(Post.user_id == current_user.id)

    if city is not None:
        statement = statement.where(Restaurant.city == city.strip().title())

    if cuisine is not None:
        statement = statement.where(func.lower(Restaurant.cuisine) == cuisine.strip().lower())

    if min_rating is not None:
        statement = statement.where(Post.rating >= min_rating)

    if tag is not None:
        statement = statement.where(Post.tags.contains([tag]))

    result = db.scalars(
        statement.order_by(desc(Post.created_at)).offset(skip).limit(limit)
    ).all()
    return [PostResponse.model_validate(post) for post in result]


@router.get("/{post_id}")
def get_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return PostResponse.model_validate(post)


@router.patch("/{post_id}")
def update_post(
    post_id: UUID,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    updates = post_update.model_dump(exclude_unset=True)
    if any(value is None for value in updates.values()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Post fields cannot be null")

    for field, value in updates.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    images.delete_image_files(post.images)
    db.delete(post)
    db.commit()


def get_owned_post(db: Session, post_id: UUID, user: User) -> Post:
    post = db.scalar(select(Post).where(Post.id == post_id, Post.user_id == user.id))
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


def get_owned_image(db: Session, post_id: UUID, image_id: UUID, user: User) -> PostImage:
    post = get_owned_post(db, post_id, user)
    for image in post.images:
        if image.id == image_id:
            return image
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.post("/{post_id}/images", status_code=status.HTTP_201_CREATED)
async def upload_post_image(
    post_id: UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostResponse:
    post = get_owned_post(db, post_id, current_user)

    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Image is larger than 5 MB")

    try:
        images.add_image(db, post, data)
    except images.ImageError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error))

    return PostResponse.model_validate(post)


@router.get("/{post_id}/images/{image_id}")
def get_post_image(
    post_id: UUID,
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    image = get_owned_image(db, post_id, image_id, current_user)
    return FileResponse(images.image_path(image), media_type=image.content_type)


@router.delete("/{post_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_image(
    post_id: UUID,
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = get_owned_image(db, post_id, image_id, current_user)
    images.delete_image(db, image)
