# We need users for authentication + roles (security marks + later audit logs)

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="analyst", nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)