from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from datetime import datetime, timezone
from starlette.concurrency import run_in_threadpool
from uuid import uuid4
import os

from app.api.dependencies import get_current_user
from app.services import media_service, media_storage
from app.core.config import settings

router = APIRouter(prefix="/media", tags=["media"])
CONTENT_TYPE_EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'video/mp4': '.mp4',
    'video/quicktime': '.mov',
    'video/webm': '.webm',
}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename is required")

    original_name = os.path.basename(file.filename)
    content_type = file.content_type or 'application/octet-stream'
    extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
    if extension is None:
        raise HTTPException(status_code=400, detail='unsupported media type')

    file.file.seek(0, os.SEEK_END)
    size_bytes = file.file.tell()
    file.file.seek(0)
    if size_bytes > settings.max_media_upload_bytes:
        raise HTTPException(status_code=413, detail='media file is too large')
    if size_bytes == 0:
        raise HTTPException(status_code=400, detail='media file is empty')

    now = datetime.now(timezone.utc)
    storage_key = f'uploads/{now:%Y/%m}/{uuid4().hex}{extension}'

    try:
        stored = await run_in_threadpool(media_storage.store, file.file, storage_key, content_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="media storage is temporarily unavailable") from exc

    try:
        record = media_service.upload_file(stored.key, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record['url'] = stored.url
    record['storageKey'] = stored.key
    record['originalFilename'] = original_name
    record['uploadedBy'] = current_user
    return {"mediaType": record['mediaType'], "url": record['url'], "media": record}
