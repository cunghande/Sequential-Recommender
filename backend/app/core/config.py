from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"
ML_DIR = PROJECT_ROOT / "ml"


class Settings:
    """Tap trung cac bien cau hinh de router/service khong doc env truc tiep."""

    app_name = "SeqRec AI API"
    app_version = "2.0"
    jwt_secret = os.getenv("JWT_SECRET", "seqrec-super-secret-key-2026")
    jwt_algorithm = "HS256"
    jwt_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    checkpoint_dir = Path(os.getenv("CHECKPOINT_DIR", ML_DIR / "checkpoints"))


settings = Settings()

