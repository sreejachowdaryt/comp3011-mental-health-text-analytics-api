from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user

from app.models.post import Post
from app.models.prediction import Prediction

from app.schemas.post import PostCreate, PostUpdate, PostResponse
from app.schemas.prediction import PredictionBasicResponse

from app.services.predictor import predict_text
from app.models.user import User


# Protect all /posts endpoints with JWT
router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(get_current_user)]
)

# Creates a new Post + auto-predict
@router.post("/", response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    # 1) Store the post text in the database
    db_post = Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    # 2) Run ML prediction using the saved post text
    label, confidence = predict_text(db_post.text)

    # 3) Store the prediction linked to the post
    #    text_snapshot stores the exact text used at prediction time (audit trail)
    pred = Prediction(
        post_id=db_post.id,
        label=label,
        confidence=confidence,
        model_version="logreg-tfidf-v1",
        text_snapshot=db_post.text,
    )
    db.add(pred)
    db.commit()

    # 4) Return the created post (prediction can be viewed via prediction endpoints)
    return db_post


# Read endpoints
@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/", response_model=list[PostResponse])
def list_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()


# Prediction endpoint (per post)
@router.get("/{post_id}/prediction/latest", response_model=PredictionBasicResponse)
def latest_prediction(post_id: int, db: Session = Depends(get_db)):
    # Ensure the post exists (clear error message)
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get most recent prediction for this post
    pred = (
        db.query(Prediction)
        .filter(Prediction.post_id == post_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    if not pred:
        raise HTTPException(status_code=404, detail="No prediction found for this post")
    return pred


@router.get("/{post_id}/prediction/history", response_model=list[PredictionBasicResponse])
def prediction_history(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Return all prediction rows for this post (newest first)
    preds = (
        db.query(Prediction)
        .filter(Prediction.post_id == post_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    if not preds:
        raise HTTPException(status_code=404, detail="No predictions found for this post")
    return preds


# Update a post + re=predict if text changed
@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post_update: PostUpdate, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    update_data = post_update.model_dump(exclude_unset=True)
    old_text = post.text  # keep old text to detect changes

    # Apply updates to the post object
    for key, value in update_data.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)

    # If text changed, generate a NEW prediction row (history preserved)
    if "text" in update_data and post.text != old_text:
        label, confidence = predict_text(post.text)
        pred = Prediction(
            post_id=post.id,
            label=label,
            confidence=confidence,
            model_version="logreg-tfidf-v1",
            text_snapshot=post.text,
        )
        db.add(pred)
        db.commit()

    return post


# Delete a post (predictions cascade delete via FK)
@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}