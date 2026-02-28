from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api.posts import router as posts_router

app = FastAPI(
    title="Mental Health Text Analytics API",
    version="0.1.0",
)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

@app.get("/health/db", tags=["system"])
def health_db():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"database": "ok"}
    finally:
        db.close()

app.include_router(posts_router)