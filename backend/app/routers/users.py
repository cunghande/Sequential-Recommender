from fastapi import APIRouter

from backend.app.services import interaction_service
from backend.app.services.recommendation_service import recommender_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/history")
def get_history(user_id: str):
    """Lay lich su xem/mua/thich cua user de hien thi trong profile."""
    history = recommender_service.get_user_history(user_id)
    if history is None:
        return {"user_id": user_id, "history": []}
    return {"user_id": user_id, "history": history}


@router.delete("/{user_id}/history/{product_asin}")
def delete_history_item(user_id: str, product_asin: str):
    """Xoa mot san pham khoi lich su va tra goi y da cap nhat."""
    return interaction_service.delete_interaction(user_id, product_asin)

