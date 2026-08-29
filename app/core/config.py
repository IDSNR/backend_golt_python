import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "partnerhub-python-backend"
    port: int = int(os.getenv("PORT", "8000"))
    frontend_origins: List[str] = None
    media_folder: str = os.getenv("MEDIA_FOLDER", str(Path(__file__).resolve().parents[2] / "media_files"))
    media_url_path: str = os.getenv("MEDIA_URL_PATH", "/media/files")
    max_media_upload_bytes: int = int(os.getenv("MAX_MEDIA_UPLOAD_BYTES", str(200 * 1024 * 1024)))
    media_storage_backend: str = os.getenv("MEDIA_STORAGE_BACKEND", "local").lower()
    media_cdn_base_url: str | None = os.getenv("MEDIA_CDN_BASE_URL")
    object_storage_bucket: str | None = os.getenv("OBJECT_STORAGE_BUCKET")
    object_storage_region: str | None = os.getenv("OBJECT_STORAGE_REGION")
    object_storage_endpoint_url: str | None = os.getenv("OBJECT_STORAGE_ENDPOINT_URL")
    object_storage_access_key_id: str | None = os.getenv("OBJECT_STORAGE_ACCESS_KEY_ID")
    object_storage_secret_access_key: str | None = os.getenv("OBJECT_STORAGE_SECRET_ACCESS_KEY")
    expo_push_url: str = os.getenv("EXPO_PUSH_URL", "https://exp.host/--/api/v2/push/send")
    expo_push_access_token: str | None = os.getenv("EXPO_PUSH_ACCESS_TOKEN")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/golt")
    db_auto_create: bool = os.getenv("DB_AUTO_CREATE", "false").lower() == "true"

    def __post_init__(self):
        if self.media_storage_backend not in {"local", "s3"}:
            raise ValueError("MEDIA_STORAGE_BACKEND must be 'local' or 's3'")
        if self.frontend_origins is None:
            raw = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
            object.__setattr__(self, "frontend_origins", [origin.strip() for origin in raw.split(",") if origin.strip()])


settings = Settings()
