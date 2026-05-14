from typing import Optional

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    """Du lieu dang ky tai khoan moi."""

    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    """Du lieu dang nhap bang email hoac user_id."""

    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    """Du lieu cap nhat ten hien thi va avatar."""

    full_name: str
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Du lieu doi mat khau khi user da dang nhap."""

    old_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    """Email nhan link dat lai mat khau."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Token reset va mat khau moi."""

    token: str
    new_password: str

