from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.dependencies import get_optional_user
from backend.app.schemas.interaction import InteractionRequest
from backend.app.services import interaction_service

router = APIRouter(tags=["interactions"])


@router.post("/interaction")
def record_interaction(req: InteractionRequest, current_user: Optional[str] = Depends(get_optional_user)):
    """Ghi hanh vi view/cart/purchase/like/rate va tra goi y moi."""
    user_id = current_user or req.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="Can user_id hoac token de ghi nhan tuong tac")
    if req.action_type not in ("view", "cart", "purchase", "like", "rate"):
        raise HTTPException(status_code=400, detail="action_type phai la view, cart, purchase, like hoac rate")
    if req.action_type == "rate" and (req.rating is None or not (1 <= req.rating <= 5)):
        raise HTTPException(status_code=400, detail="Rating phai tu 1 den 5")
    return interaction_service.record_interaction(user_id, req.product_asin, req.action_type, req.rating)

