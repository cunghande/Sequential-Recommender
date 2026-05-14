from backend.app.db.queries import fetch_categories, fetch_products
from backend.app.services.recommendation_service import recommender_service


def list_products(category: str | None, search: str | None, page: int, limit: int) -> dict:
    """Tra danh sach san pham cho trang Products."""
    return fetch_products(category, search, page, limit)


def list_categories() -> dict:
    """Tra danh sach loai hang de frontend tao filter."""
    return {"categories": fetch_categories()}


def get_product_detail(asin: str) -> dict | None:
    """Lay chi tiet san pham tu MySQL, fallback metadata checkpoint neu can."""
    return recommender_service.get_product_detail(asin)

