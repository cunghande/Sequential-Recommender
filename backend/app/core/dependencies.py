from typing import Optional

from fastapi import Header, HTTPException

from backend.app.core.security import decode_jwt


def get_current_user(authorization: str = Header(None)) -> str:
    """Bat buoc co Bearer token va tra ve user_id hien tai."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Chua xac thuc")
    token = authorization.split(" ", 1)[1]
    user_id = decode_jwt(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token khong hop le hoac da het han")
    return user_id


def get_optional_user(authorization: str = Header(None)) -> Optional[str]:
    """Doc user_id neu co token; endpoint public co the tra ve None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    return decode_jwt(token)

