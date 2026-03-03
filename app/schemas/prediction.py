from pydantic import BaseModel
from datetime import datetime

class PostMini(BaseModel):
    id: int
    text: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    id: int
    post_id: int
    label: str
    confidence: float | None
    model_version: str
    created_at: datetime
    post: PostMini

    class Config:
        from_attributes = True