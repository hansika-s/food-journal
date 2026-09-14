from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    restaurant_name: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    cuisine: Mapped[str] = mapped_column(String)
    rating: Mapped[int] = mapped_column()
    notes: Mapped[str] = mapped_column(String)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))