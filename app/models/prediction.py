# Predictions gives you analytics and intelligence features 

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False)

    label: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="v0", nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    post = relationship("Post", back_populates="predictions")