import secrets
import time

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.dependencies import get_current_user
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
)
from backend.app.services import auth_service, session_service
from backend.app.services.recommendation_service import recommender_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(req: RegisterRequest):
    """Dang ky user moi va tra JWT de frontend dang nhap ngay."""
    existing = auth_service.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email da duoc su dung")
    user_id = f"u_{int(time.time() * 1000)}_{secrets.token_hex(3)}"
    password_hash = auth_service.hash_password(req.password)
    auth_service.create_user(user_id, req.email, req.full_name, password_hash)
    token = auth_service.create_jwt(user_id)
    return {"token": token, "user": {"user_id": user_id, "email": req.email, "full_name": req.full_name}}


@router.post("/login")
def login(req: LoginRequest):
    """Dang nhap bang email hoac dataset user_id va khoi tao session goi y."""
    user = auth_service.get_user_by_login_identifier(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoac user_id khong ton tai")
    if not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Tai khoan demo khong ho tro dang nhap bang mat khau")
    if not auth_service.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Mat khau khong dung")
    token = auth_service.create_jwt(user["user_id"])
    db_history = recommender_service.get_user_history_from_db(user["user_id"])
    if db_history:
        session_service.init_sequence(user["user_id"], db_history)
    return {
        "token": token,
        "user": {"user_id": user["user_id"], "email": user["email"], "full_name": user.get("full_name", "")},
    }


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    """Tra thong tin user hien tai tu JWT."""
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User khong ton tai")
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "avatar_url": user.get("avatar_url", ""),
        "created_at": str(user.get("created_at", "")),
    }


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, user_id: str = Depends(get_current_user)):
    """Cap nhat ten hien thi va avatar cua user."""
    auth_service.update_profile(user_id, req.full_name, req.avatar_url)
    return {"message": "Cap nhat thanh cong"}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, user_id: str = Depends(get_current_user)):
    """Doi mat khau khi user da biet mat khau cu."""
    user = auth_service.get_user_by_id(user_id)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="Khong the doi mat khau tai khoan nay")
    if not auth_service.verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Mat khau cu khong dung")
    auth_service.update_password(user_id, auth_service.hash_password(req.new_password))
    return {"message": "Doi mat khau thanh cong"}


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """Tao token reset va gui email neu user ton tai."""
    user = auth_service.get_user_by_email(req.email)
    if not user:
        return {"message": "Neu email ton tai, chung toi da gui link dat lai mat khau."}
    token = secrets.token_urlsafe(32)
    auth_service.save_reset_token(user["user_id"], token)
    if not auth_service.send_reset_email(req.email, token):
        raise HTTPException(status_code=500, detail="Khong the gui email. Vui long thu lai sau.")
    return {"message": "Link dat lai mat khau da duoc gui toi email cua ban."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    """Dat lai mat khau bang reset token con han."""
    user = auth_service.get_user_by_reset_token(req.token)
    if not user:
        raise HTTPException(status_code=400, detail="Token khong hop le hoac da het han")
    auth_service.update_password(user["user_id"], auth_service.hash_password(req.new_password))
    return {"message": "Dat lai mat khau thanh cong! Ban co the dang nhap ngay."}


@router.post("/logout")
def logout(user_id: str = Depends(get_current_user)):
    """Xoa sequence tam trong session khi user dang xuat."""
    session_service.clear_sequence(user_id)
    return {"message": "Dang xuat thanh cong"}

