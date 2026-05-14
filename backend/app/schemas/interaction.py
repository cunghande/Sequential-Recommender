from typing import Optional

from pydantic import BaseModel


class InteractionRequest(BaseModel):
    """Hanh vi cua user voi san pham de luu DB va cap nhat goi y realtime."""

    product_asin: str
    action_type: str
    rating: Optional[float] = None
    user_id: Optional[str] = None

