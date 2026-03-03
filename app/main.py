from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api.posts import router as posts_router
from app.api.auth import router as auth_router
from pydantic import BaseModel
from app.services.predictor import predict_text

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.models.post import Post
from app.models.prediction import Prediction
from app.services.predictor import predict_text
from pydantic import BaseModel
from app.api.predictions import router as predictions_router

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

app.include_router(auth_router)

app.include_router(posts_router)

class PredictRequest(BaseModel):
    text: str

class PredictRequest(BaseModel):
    text: str

@app.post("/predict", tags=["predict"])
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    label, confidence = predict_text(req.text)

    # 1) create a post row (stores the input text once)
    post = Post(text=req.text, source="predict")
    db.add(post)
    db.commit()
    db.refresh(post)

    # 2) create prediction row linked to that post
    pred = Prediction(
        post_id=post.id,
        label=label,
        confidence=confidence,
        model_version="logreg-tfidf-v1",
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)

    # optional uncertainty flag (choose threshold you want)
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

app.include_router(predictions_router)