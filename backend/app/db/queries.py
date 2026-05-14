from backend.app.db.connection import get_connection


def fetch_products(category: str | None, search: str | None, page: int, limit: int) -> dict:
    """Lay danh sach san pham co tim kiem va phan trang tu MySQL."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []
        if category:
            where_clauses.append("category = %s")
            params.append(category)
        if search:
            where_clauses.append("title LIKE %s")
            params.append(f"%{search}%")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        offset = (page - 1) * limit
        cursor.execute(f"SELECT COUNT(*) as total FROM products {where_sql}", params)
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"SELECT product_id as asin, title, category, price, image_url as img_url FROM products {where_sql} LIMIT %s OFFSET %s",
            params + [limit, offset],
        )
        products = cursor.fetchall()
        cursor.close()
        return {"total": total, "page": page, "limit": limit, "products": products}
    finally:
        conn.close()


def fetch_categories() -> list[str]:
    """Lay danh sach category hien co trong bang products."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return categories
    finally:
        conn.close()

