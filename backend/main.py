"""
Main FastAPI application — SeqRec AI Backend
Bao gồm đầy đủ: Auth, Interaction, Recommendation, Products
"""
import secrets
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from backend.services.recommender import recommender_service
from backend.services import session as sess_mgr
from backend.services import auth as auth_svc
from backend.services.db import get_connection

app = FastAPI(title="SeqRec AI API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth Dependency ──────────────────────────────────────────────────────────
def get_current_user(authorization: str = Header(None)) -> str:
    """Lấy user_id từ JWT Bearer token trong header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Chưa xác thực")
    token = authorization.split(" ", 1)[1]
    user_id = auth_svc.decode_jwt(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")
    return user_id

def get_optional_user(authorization: str = Header(None)) -> Optional[str]:
    """Lấy user_id không bắt buộc (cho endpoint public)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    return auth_svc.decode_jwt(token)


# ─── Pydantic Models ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateProfileRequest(BaseModel):
    full_name: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class InteractionRequest(BaseModel):
    product_asin: str
    action_type: str          # "view" | "rate"
    rating: Optional[float] = None

class SequenceRecommendRequest(BaseModel):
    sequence: List[int]
    top_k: Optional[int] = 12

class RecommendRequest(BaseModel):
    sequence_history: List[int]
    top_k: Optional[int] = 10


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    sample_ids = list(recommender_service.train_data.keys())[:10]
    return {"status": "online", "demo_users": sample_ids}

@app.get("/stats")
def get_stats():
    return {"results": recommender_service.get_stats()}


# ─── Auth Endpoints ───────────────────────────────────────────────────────────
@app.post("/auth/register")
def register(req: RegisterRequest):
    existing = auth_svc.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email đã được sử dụng")

    # Tạo user_id tự động dạng số (lấy từ DB)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    user_id = str(count + 1000)  # bắt đầu từ 1000 để không trùng demo users

    hashed = auth_svc.hash_password(req.password)
    auth_svc.create_user(user_id, req.email, req.full_name, hashed)

    token = auth_svc.create_jwt(user_id)
    return {
        "token": token,
        "user": {"user_id": user_id, "email": req.email, "full_name": req.full_name}
    }


@app.post("/auth/login")
def login(req: LoginRequest):
    user = auth_svc.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email không tồn tại")
    if not user.get('password_hash'):
        raise HTTPException(status_code=401, detail="Tài khoản demo — không hỗ trợ đăng nhập bằng mật khẩu")
    if not auth_svc.verify_password(req.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Mật khẩu không đúng")

    token = auth_svc.create_jwt(user['user_id'])

    # Khởi tạo session từ lịch sử DB
    db_hist = recommender_service.get_user_history_from_db(user['user_id'])
    if db_hist:
        sess_mgr.init_sequence(user['user_id'], db_hist)

    return {
        "token": token,
        "user": {
            "user_id": user['user_id'],
            "email": user['email'],
            "full_name": user.get('full_name', '')
        }
    }


@app.get("/auth/me")
def get_me(user_id: str = Depends(get_current_user)):
    user = auth_svc.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    return {
        "user_id": user['user_id'],
        "email": user['email'],
        "full_name": user.get('full_name', ''),
        "created_at": str(user.get('created_at', ''))
    }


@app.put("/auth/profile")
def update_profile(req: UpdateProfileRequest, user_id: str = Depends(get_current_user)):
    auth_svc.update_profile(user_id, req.full_name)
    return {"message": "Cập nhật thành công"}


@app.post("/auth/change-password")
def change_password(req: ChangePasswordRequest, user_id: str = Depends(get_current_user)):
    user = auth_svc.get_user_by_id(user_id)
    if not user or not user.get('password_hash'):
        raise HTTPException(status_code=400, detail="Không thể đổi mật khẩu tài khoản này")
    if not auth_svc.verify_password(req.old_password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Mật khẩu cũ không đúng")
    new_hash = auth_svc.hash_password(req.new_password)
    auth_svc.update_password(user_id, new_hash)
    return {"message": "Đổi mật khẩu thành công"}


@app.post("/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    user = auth_svc.get_user_by_email(req.email)
    if not user:
        # Không tiết lộ email có tồn tại không (bảo mật)
        return {"message": "Nếu email tồn tại, chúng tôi đã gửi link đặt lại mật khẩu."}

    token = secrets.token_urlsafe(32)
    auth_svc.save_reset_token(user['user_id'], token)
    sent = auth_svc.send_reset_email(req.email, token)

    if not sent:
        raise HTTPException(status_code=500, detail="Không thể gửi email. Vui lòng thử lại sau.")
    return {"message": "Link đặt lại mật khẩu đã được gửi tới email của bạn."}


@app.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest):
    user = auth_svc.get_user_by_reset_token(req.token)
    if not user:
        raise HTTPException(status_code=400, detail="Token không hợp lệ hoặc đã hết hạn")
    new_hash = auth_svc.hash_password(req.new_password)
    auth_svc.update_password(user['user_id'], new_hash)
    return {"message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay."}


@app.post("/auth/logout")
def logout(user_id: str = Depends(get_current_user)):
    sess_mgr.clear_sequence(user_id)
    return {"message": "Đăng xuất thành công"}


# ─── Products ─────────────────────────────────────────────────────────────────
@app.get("/products")
def get_products(category: Optional[str] = None, search: Optional[str] = None,
                 page: int = 1, limit: int = 20):
    """Danh sách sản phẩm với tìm kiếm và phân trang."""
    try:
        conn = get_connection()
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
        total = cursor.fetchone()['total']

        cursor.execute(
            f"SELECT product_id as asin, title, category, price, image_url as img_url FROM products {where_sql} LIMIT %s OFFSET %s",
            params + [limit, offset]
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return {"total": total, "page": page, "limit": limit, "products": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/categories")
def get_categories():
    """Danh sách tất cả categories."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category")
        cats = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"categories": cats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{asin}")
def get_product(asin: str):
    """Chi tiết một sản phẩm."""
    detail = recommender_service.get_product_detail(asin)
    if not detail:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return detail


# ─── Interaction ──────────────────────────────────────────────────────────────
@app.post("/interaction")
def record_interaction(req: InteractionRequest, user_id: str = Depends(get_current_user)):
    """
    Ghi nhận hành vi người dùng → cập nhật session → trả gợi ý mới.
    Use Case 2 (view) & Use Case 3 (rating >= 4).
    """
    if req.action_type not in ("view", "rate"):
        raise HTTPException(status_code=400, detail="action_type phải là 'view' hoặc 'rate'")
    if req.action_type == "rate" and (req.rating is None or not (1 <= req.rating <= 5)):
        raise HTTPException(status_code=400, detail="Rating phải từ 1 đến 5")

    result = recommender_service.record_interaction(
        user_id, req.product_asin, req.action_type, req.rating
    )
    recommender_service.invalidate_popular_cache()
    return result


# ─── Recommendations ──────────────────────────────────────────────────────────
@app.get("/recommend")
def recommend_for_user(user_id: Optional[str] = None, top_k: int = 12,
                       current_user: Optional[str] = Depends(get_optional_user)):
    """
    Gợi ý theo user:
    - Nếu có JWT → dùng user từ token
    - Nếu truyền user_id (demo) → dùng user_id đó
    - Nếu không có gì → trả popular
    """
    uid = current_user or user_id
    if not uid:
        return {"source": "popular", "recommendations": recommender_service.get_popular_products(top_k)}
    return recommender_service.get_recommendations_for_user(uid, top_k)


@app.get("/recommend/popular")
def popular_products(top_k: int = 12):
    """Top sản phẩm phổ biến nhất (Use Case 1 - User mới)."""
    return {"recommendations": recommender_service.get_popular_products(top_k)}


@app.post("/recommend/sequence")
def recommend_from_sequence(req: SequenceRecommendRequest):
    """
    Realtime demo (Use Case 5):
    Nhận sequence tạm → predict → trả kết quả. KHÔNG lưu DB.
    """
    recs = recommender_service.get_recommendations(req.sequence, req.top_k)
    return {"source": "realtime_demo", "recommendations": recs}


# ─── Legacy endpoints (giữ tương thích Frontend cũ) ──────────────────────────
@app.post("/recommend")
def recommend_legacy(req: RecommendRequest):
    if not req.sequence_history:
        raise HTTPException(status_code=400, detail="Chuỗi lịch sử không được trống")
    recs = recommender_service.get_recommendations(req.sequence_history, req.top_k)
    return {"recommendations": recs}


@app.get("/users/{user_id}/history")
def get_history(user_id: str):
    history = recommender_service.get_user_history(user_id)
    if history is None:
        return {"user_id": user_id, "history": []}
    return {"user_id": user_id, "history": history}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)