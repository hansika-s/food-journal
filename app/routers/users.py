from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Post, User
from app.schemas.users import DeleteAccountRequest, UserResponse
from app.security import verify_password
from app.services import images, restaurants

router = APIRouter(
    prefix="/api/users/me",
    tags=["Users"]
)


@router.get("")
def get_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    restaurant_ids = set(db.scalars(select(Post.restaurant_id).where(Post.user_id == current_user.id)).all())
    images.delete_image_files_for_user(db, current_user.id)
    db.delete(current_user)
    db.commit()
    restaurants.delete_unused_restaurants(db, restaurant_ids)
