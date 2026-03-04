from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    label = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)

    model_version = Column(String(50), nullable=False, default="logreg-tfidf-v1")
    
    # ✅ NEW: stores the exact text used for this prediction at that time
    text_snapshot = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Optional relationship (recommended)
    post = relationship("Post", back_populates="predictions")