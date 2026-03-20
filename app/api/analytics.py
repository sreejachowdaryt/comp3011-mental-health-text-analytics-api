from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.post import Post
from app.models.prediction import Prediction
from app.schemas.analytics import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    total_posts = db.query(Post).count()
    total_predictions = db.query(Prediction).count()

    depression_count = db.query(Prediction).filter(Prediction.label == "Depression").count()
    anxiety_count = db.query(Prediction).filter(Prediction.label == "Anxiety").count()
    normal_count = db.query(Prediction).filter(Prediction.label == "Normal").count()

    if total_predictions == 0:
        depression_percentage = 0.0
        anxiety_percentage = 0.0
        normal_percentage = 0.0
    else:
        depression_percentage = round((depression_count / total_predictions) * 100, 2)
        anxiety_percentage = round((anxiety_count / total_predictions) * 100, 2)
        normal_percentage = round((normal_count / total_predictions) * 100, 2)

    return {
        "total_posts": total_posts,
        "total_predictions": total_predictions,
        "depression_count": depression_count,
        "anxiety_count": anxiety_count,
        "normal_count": normal_count,
        "depression_percentage": depression_percentage,
        "anxiety_percentage": anxiety_percentage,
        "normal_percentage": normal_percentage,
    }