# All database tables will inherit from Base. Alembic uses this to generate migrations. 

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass