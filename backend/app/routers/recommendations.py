from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.dependencies import get_optional_user
from backend.app.schemas.recommendation import RecommendRequest, SequenceRecommendRequest
from backend.app.services.recommendation_service import recommender_service

router = APIRouter(tags=["recommendations"])


@router.get("/recommend")
def recommend_for_user(user_id: Optional[str] = None, top_k: int = 12, current_user: Optional[str] = Depends(get_optional_user)):
    """Goi y theo user; user moi se fallback ve san pham pho bien."""
    uid = current_user or user_id
    if not uid:
        return {"source": "popular", "recommendations": recommender_service.get_popular_products(top_k)}
    return recommender_service.get_recommendations_for_user(uid, top_k)


@router.get("/recommend/popular")
def popular_products(top_k: int = 12):
    """Tra top san pham pho bien cho cold-start user."""
    return {"recommendations": recommender_service.get_popular_products(top_k)}


@router.post("/recommend/sequence")
def recommend_from_sequence(req: SequenceRecommendRequest):
    """Goi y realtime tu sequence tam, khong luu vao database."""
    recs = recommender_service.get_recommendations(req.sequence, req.top_k)
    return {"source": "realtime_demo", "recommendations": recs}


@router.post("/recommend")
def recommend_legacy(req: RecommendRequest):
    """Endpoint cu de frontend cu gui sequence_history."""
    if not req.sequence_history:
        raise HTTPException(status_code=400, detail="Chuoi lich su khong duoc trong")
    recs = recommender_service.get_recommendations(req.sequence_history, req.top_k)
    return {"recommendations": recs}

