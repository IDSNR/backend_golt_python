from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from uuid import uuid4
from pathlib import Path
import os

from app.api.dependencies import get_current_user
from app.services import media_service
from app.core.config import settings

router = APIRouter(prefix="/media", tags=["media"])
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'video/mp4', 'video/quicktime', 'video/webm',
}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename is required")

    # Ensure media folder exists
    media_dir = Path(settings.media_folder)
    media_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename).name
    content_type = file.content_type or 'application/octet-stream'
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail='unsupported media type')
    new_filename = f'{uuid4().hex}{Path(original_name).suffix.lower()}'
    dest_path = media_dir / new_filename

    try:
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_BYTES:
            raise ValueError('media file is too large')
        with open(dest_path, "wb") as fh:
            fh.write(contents)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="failed to save uploaded file") from exc

    # Persist metadata (media_service will try DB and/or in-memory)
    try:
        record = media_service.upload_file(new_filename, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Return a path that the frontend can use (served by static mount)
    url = f"{settings.media_url_path}/{new_filename}"

    record['url'] = url

    record['originalFilename'] = original_name
    record['uploadedBy'] = current_user
    return {"mediaType": record['mediaType'], "url": record['url'], "media": record}
