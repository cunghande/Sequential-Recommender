from typing import Optional

from pydantic import BaseModel


class ProductResponse(BaseModel):
    """Thong tin san pham tra ve cho frontend."""

    asin: str
    title: str
    category: Optional[str] = None
    price: Optional[float] = None
    img_url: Optional[str] = None

