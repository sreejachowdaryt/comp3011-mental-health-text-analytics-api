from pydantic import BaseModel

class AnalyticsSummary(BaseModel):
    total_posts: int
    total_predictions: int
    depression_count: int
    anxiety_count: int
    normal_count: int
    depression_percentage: float
    anxiety_percentage: float
    normal_percentage: float