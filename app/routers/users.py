from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.users import DeleteAccountRequest
from app.security import verify_password

router = APIRouter(
    prefix="/api/users/me",
    tags=["Users"]
)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    db.delete(current_user)
    db.commit()
