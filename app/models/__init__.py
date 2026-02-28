# This makes Alembic "see" all models easily when importing metadata

from app.models.user import User
from app.models.post import Post
from app.models.prediction import Prediction

__all__ = ["User", "Post", "Prediction"]