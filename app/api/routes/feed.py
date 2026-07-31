from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services import content_service

router = APIRouter(prefix="/feed", tags=["feed"])


class FeedViewRequest(BaseModel):
    completed: bool = False


@router.get("")
def get_feed() -> dict:
    return {"feed": content_service.list_public_posts()}


@router.post("/{content_id}/view", status_code=status.HTTP_201_CREATED)
def record_feed_view(content_id: str, payload: FeedViewRequest, current_user: str = Depends(get_current_user)) -> dict:
    post = content_service.get_post(content_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Content not found")

    post['views'] = post.get('views', 0) + 1
    if payload.completed:
        post['completions'] = post.get('completions', 0) + 1
    return {"recorded": True}
