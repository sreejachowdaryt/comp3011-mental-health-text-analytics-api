'''
Why?
1. Validate incoming request data 
2. Control outgoing response format 
3. Prevent exposing internal DB fields accidently

'''

from pydantic import BaseModel
from datetime import datetime

class PostBase(BaseModel):
    text: str
    source: str

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    text: str | None = None
    source: str | None = None

class PostResponse(PostBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True