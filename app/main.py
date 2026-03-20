from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.db.session import SessionLocal
from app.db.deps import get_db
from app.api.auth import router as auth_router
from app.api.posts import router as posts_router
from app.api.predictions import router as predictions_router
from app.models.post import Post
from app.models.prediction import Prediction
from app.services.predictor import predict_text
from app.api.analytics import router as analytics_router

# ── Rate Limiter setup ──
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Mental Health Text Analytics API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Health Checks ──
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

# ── Routers ──
app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(predictions_router)

# ── Direct Predict Endpoint (rate limited) ──
class PredictRequest(BaseModel):
    text: str

@app.post("/predict", tags=["quick predict"])
@limiter.limit("10/minute")
def predict(request: Request, req: PredictRequest, db: Session = Depends(get_db)):
    label, confidence = predict_text(req.text)

    post = Post(text=req.text, source="predict")
    db.add(post)
    db.commit()
    db.refresh(post)

    pred = Prediction(
        post_id=post.id,
        label=label,
        confidence=confidence,
        model_version="logreg-tfidf-v1",
        text_snapshot=req.text,
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)

    uncertain = confidence is not None and confidence < 0.40

    return {
        "post_id": post.id,
        "prediction_id": pred.id,
        "label": label,
        "confidence": confidence,
        "uncertain": uncertain,
        "model_version": pred.model_version,
        "created_at": pred.created_at,
    }

app.include_router(analytics_router)

# ── Frontend ──
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("static/index.html")