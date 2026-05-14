from backend.app.services.recommendation_service import recommender_service


def record_interaction(user_id: str, product_asin: str, action_type: str, rating: float | None) -> dict:
    """Luu hanh vi user va lam moi cache popular de goi y cap nhat."""
    result = recommender_service.record_interaction(user_id, product_asin, action_type, rating)
    recommender_service.invalidate_popular_cache()
    return result


def delete_interaction(user_id: str, product_asin: str) -> dict:
    """Xoa mot san pham khoi lich su va tinh lai goi y."""
    result = recommender_service.delete_interaction(user_id, product_asin)
    recommender_service.invalidate_popular_cache()
    return result

