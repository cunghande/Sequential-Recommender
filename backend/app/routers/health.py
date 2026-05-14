from fastapi import APIRouter

from backend.app.services.recommendation_service import recommender_service

router = APIRouter(tags=["health"])


@router.get("/")
def root():
    """Kiem tra backend online va tra ve mot so demo user co san."""
    sample_ids = list(recommender_service.train_data.keys())[:10]
    return {"status": "online", "demo_users": sample_ids}


@router.get("/stats")
def get_stats():
    """Tra thong ke model, checkpoint va du lieu dang nap trong backend."""
    return {"results": recommender_service.get_stats()}

