from .service import MediaService
from .storage import build_media_storage
from app.core.config import settings

media_service = MediaService()
media_storage = build_media_storage(settings)
