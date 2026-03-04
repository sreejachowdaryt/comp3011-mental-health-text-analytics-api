from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionResponse
from app.core.deps import get_current_user

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=list[PredictionResponse])
def list_predictions(db: Session = Depends(get_db), limit: int = 50):
    qs = (
        db.query(Prediction)
        .options(joinedload(Prediction.post))
        # DISTINCT ON requires ORDER BY starts with the distinct column
        .order_by(Prediction.post_id, Prediction.created_at.desc())
        .distinct(Prediction.post_id)
        .limit(limit)
        .all()
    )
    return qs

@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    pred = (
        db.query(Prediction)
        .options(joinedload(Prediction.post))
        .filter(Prediction.id == prediction_id)
        .first()
    )
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return pred