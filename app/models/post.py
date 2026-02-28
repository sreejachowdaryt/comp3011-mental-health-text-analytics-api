# Posts gives CRUD

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="unknown", index=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    predictions = relationship("Prediction", back_populates="post", cascade="all, delete-orphan")