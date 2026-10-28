from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_posts_rating_range"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    restaurant_name: Mapped[str]
    city: Mapped[str]
    cuisine: Mapped[str]
    rating: Mapped[int]
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )