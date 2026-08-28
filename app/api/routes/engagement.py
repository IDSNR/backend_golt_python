from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_optional_user
from app.services import content_access_service, content_service
from app.modules.engagement import EngagementService

router = APIRouter(prefix="/content", tags=["engagement"])
engagement_service = EngagementService()


class CommentCreateRequest(BaseModel):
    body: str
    parentCommentId: str | None = None


def _require_content(content_id: str, current_user: str | None) -> dict:
    post = content_service.get_post(content_id)
    if post is None or not content_access_service.can_view_post(current_user, post):
        raise HTTPException(status_code=404, detail="Content not found")
    return post


@router.get("/{content_id}/engagement")
def get_engagement(content_id: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    _require_content(content_id, current_user)
    return {"engagement": engagement_service.get_summary(content_id, current_user)}


@router.post("/{content_id}/like", status_code=status.HTTP_200_OK)
def like_content(content_id: str, current_user: str = Depends(get_current_user)) -> dict:
    _require_content(content_id, current_user)
    return {"engagement": engagement_service.like(current_user, content_id)}


@router.delete("/{content_id}/like")
def unlike_content(content_id: str, current_user: str = Depends(get_current_user)) -> dict:
    _require_content(content_id, current_user)
    return {"engagement": engagement_service.unlike(current_user, content_id)}


@router.post("/{content_id}/bookmark", status_code=status.HTTP_200_OK)
def bookmark_content(content_id: str, current_user: str = Depends(get_current_user)) -> dict:
    _require_content(content_id, current_user)
    return {"engagement": engagement_service.bookmark(current_user, content_id)}


@router.delete("/{content_id}/bookmark")
def unbookmark_content(content_id: str, current_user: str = Depends(get_current_user)) -> dict:
    _require_content(content_id, current_user)
    return {"engagement": engagement_service.unbookmark(current_user, content_id)}


@router.post("/{content_id}/share", status_code=status.HTTP_201_CREATED)
def share_content(content_id: str, current_user: str = Depends(get_current_user)) -> dict:
    _require_content(content_id, current_user)
    return {"share": engagement_service.share(current_user, content_id)}


@router.get("/{content_id}/comments")
def list_comments(content_id: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    _require_content(content_id, current_user)
    return {"comments": engagement_service.list_comments(content_id)}


@router.post("/{content_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(content_id: str, payload: CommentCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    _require_content(content_id, current_user)
    try:
        comment = engagement_service.add_comment(current_user, content_id, payload.body, payload.parentCommentId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"comment": comment}
