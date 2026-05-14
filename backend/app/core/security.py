from backend.services import auth as auth_service


def hash_password(plain: str) -> str:
    """Bam mat khau truoc khi luu vao bang users."""
    return auth_service.hash_password(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Kiem tra mat khau nguoi dung nhap voi hash trong database."""
    return auth_service.verify_password(plain, hashed)


def create_jwt(user_id: str) -> str:
    """Tao JWT de frontend gui trong header Authorization."""
    return auth_service.create_jwt(user_id)


def decode_jwt(token: str) -> str | None:
    """Giai ma JWT va tra ve user_id neu token con hop le."""
    return auth_service.decode_jwt(token)

