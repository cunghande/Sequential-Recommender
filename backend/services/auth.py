"""
Auth service: bcrypt password hashing, JWT token, email reset password.
"""
import os
import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jwt
from passlib.context import CryptContext

from backend.services.db import get_connection

# ─── Cấu hình ────────────────────────────────────────────────────────────────
JWT_SECRET = "seqrec-super-secret-key-2026"   # Đổi thành key ngẫu nhiên trong production
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# Gmail SMTP — điền App Password 16 ký tự vào đây
GMAIL_ADDRESS  = "docung6996@gmail.com"
GMAIL_APP_PASS = "cung2004"   # ← Cần điền App Password

FRONTEND_URL = "http://localhost:5173"
# ─────────────────────────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_jwt(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt(token: str) -> str | None:
    """Trả về user_id nếu token hợp lệ, None nếu không."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ── Database helpers ──────────────────────────────────────────────────────────
def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def get_user_by_login_identifier(identifier: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE email = %s OR user_id = %s",
        (identifier, str(identifier))
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def get_user_by_id(user_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (str(user_id),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def create_user(user_id: str, email: str, full_name: str, password_hash: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (user_id, email, full_name, password_hash) VALUES (%s, %s, %s, %s)",
        (user_id, email, full_name, password_hash)
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_password(user_id: str, new_hash: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL WHERE user_id = %s",
        (new_hash, str(user_id))
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_profile(user_id: str, full_name: str, avatar_url: str | None = None) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET full_name = %s, avatar_url = COALESCE(%s, avatar_url) WHERE user_id = %s",
        (full_name, avatar_url, str(user_id))
    )
    conn.commit()
    cursor.close()
    conn.close()

def save_reset_token(user_id: str, token: str) -> None:
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reset_token = %s, reset_token_expires = %s WHERE user_id = %s",
        (token, expires, str(user_id))
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_reset_token(token: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE reset_token = %s AND reset_token_expires > NOW()",
        (token,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


# ── Email ─────────────────────────────────────────────────────────────────────
def send_reset_email(to_email: str, token: str) -> bool:
    """
    Gửi email chứa link đặt lại mật khẩu tới người dùng.
    Trả về True nếu thành công.
    """
    reset_link = f"{FRONTEND_URL}?reset_token={token}"
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🔐 Đặt lại mật khẩu — SeqRec AI"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = to_email

    html = f"""
    <html><body style="font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px;">
      <div style="max-width: 520px; margin: auto; background: #1e293b; border-radius: 16px; padding: 40px; border: 1px solid #334155;">
        <h2 style="color: #3b82f6; margin-top: 0;">🔐 Đặt lại mật khẩu</h2>
        <p>Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản <strong>{to_email}</strong>.</p>
        <p>Click vào nút bên dưới để đặt lại mật khẩu. Link có hiệu lực trong <strong>1 giờ</strong>.</p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{reset_link}" 
             style="background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; 
                    padding: 14px 32px; border-radius: 8px; text-decoration: none; 
                    font-weight: bold; font-size: 16px;">
            Đặt lại mật khẩu
          </a>
        </div>
        <p style="color: #94a3b8; font-size: 13px;">Nếu bạn không yêu cầu điều này, hãy bỏ qua email này.</p>
        <hr style="border-color: #334155; margin: 24px 0;">
        <p style="color: #64748b; font-size: 12px; text-align: center;">SeqRec AI — Sequential Recommendation System</p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False
