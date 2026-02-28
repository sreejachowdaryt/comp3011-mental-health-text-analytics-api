''' 
Why?
1. Creates the SQLAlchemy engine
2. Creates DB sessions per request 
3. Prevents connections leaks 
4. Is industry-standard structure 

'''


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()