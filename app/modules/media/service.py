from datetime import datetime, timezone
from typing import Optional


class MediaService:
    def __init__(self) -> None:
        self.media_items: list[dict] = []
        self.next_media_id = 1

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def _next_media_id(self) -> str:
        media_id = f'media-{self.next_media_id}'
        self.next_media_id += 1
        return media_id

    def upload_file(self, filename: str, content_type: str) -> dict:
        if not filename.strip():
            raise ValueError('filename is required')

        media_type = 'video' if content_type.startswith('video/') else 'image'
        media_id = self._next_media_id()
        url = f'https://partnerhub.test/media/{filename}'

        record = {
            'id': media_id,
            'filename': filename,
            'mediaType': media_type,
            'contentType': content_type,
            'url': url,
            'created_at': self._now_iso(),
        }
        # Attempt to persist media metadata to the local Postgres DB if available
        try:
            from backend.data_management.services import create_media_record
        except Exception:
            create_media_record = None

        if create_media_record is not None:
            try:
                media_obj = create_media_record(filename=filename, media_url=url, media_type=media_type, content_type=content_type)
                record['id'] = f'media-{media_obj.id}'
                record['url'] = media_obj.media_url
                record['created_at'] = media_obj.created_at.isoformat() + 'Z'
            except Exception:
                # fall back to in-memory record on any DB error
                self.media_items.append(record)
                return record
        else:
            self.media_items.append(record)

        return record

    def get_media(self, media_id: str) -> Optional[dict]:
        return next((item for item in self.media_items if item['id'] == media_id), None)

    def list_media(self) -> list[dict]:
        return list(self.media_items)
