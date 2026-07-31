from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.api.dependencies import get_optional_user

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_media(
    file: UploadFile = File(...),
    current_user: str | None = Depends(get_optional_user),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename is required")

    media_type = "video" if file.content_type.startswith("video/") else "image"
    return {
        "mediaType": media_type,
        "url": f"https://partnerhub.test/media/{file.filename}",
        "media": {
            "id": f"media-{file.filename}",
            "mediaType": media_type,
            "url": f"https://partnerhub.test/media/{file.filename}",
            "filename": file.filename,
            "contentType": file.content_type,
        },
    }
