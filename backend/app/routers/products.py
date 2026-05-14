from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def get_products(category: Optional[str] = None, search: Optional[str] = None, page: int = 1, limit: int = 20):
    """Lay danh sach san pham theo category, tu khoa va phan trang."""
    try:
        return product_service.list_products(category, search, page, limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/categories")
def get_categories():
    """Lay toan bo loai hang hien co trong database."""
    try:
        return product_service.list_categories()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{asin}")
def get_product(asin: str):
    """Lay chi tiet mot san pham theo ASIN/product_id."""
    detail = product_service.get_product_detail(asin)
    if not detail:
        raise HTTPException(status_code=404, detail="Khong tim thay san pham")
    return detail

