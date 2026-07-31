from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_optional_user
from app.services import profile_service, social_service, story_service

router = APIRouter(prefix="/stories", tags=["stories"])
service = story_service


class StoryCreateRequest(BaseModel):
    creatorId: str | None = None
    mediaType: str | None = None
    mediaUrl: str
    isSponsored: bool = False


@router.post("", status_code=status.HTTP_201_CREATED)
def create_story(payload: StoryCreateRequest, current_user: str | None = Depends(get_optional_user)) -> dict:
    creator_id = current_user or payload.creatorId
    if creator_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    if not payload.mediaUrl.strip():
        raise HTTPException(status_code=400, detail="mediaUrl is required")
    story_payload = payload.model_dump()
    story_payload.pop('creatorId', None)
    story = service.post_story(creator_id, story_payload)
    return {"story": story}


@router.get("/by/{creator_id}")
def get_stories_by_creator(creator_id: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    profile = profile_service.get_profile(creator_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    if profile.get("isPrivate") and current_user is not None:
        allowed = social_service.is_approved_follower(current_user, creator_id)
        if not allowed:
            raise HTTPException(status_code=403, detail="This account is private")
    elif profile.get("isPrivate") and current_user is None:
        raise HTTPException(status_code=403, detail="This account is private")

    stories = service.get_active_stories(creator_id)
    return {"stories": stories}


@router.post("/{story_id}/view", status_code=status.HTTP_201_CREATED)
def record_story_view(story_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        service.record_story_view(story_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"recorded": True}


@router.get("/{story_id}/viewers")
def get_story_viewers(story_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        viewers = service.get_story_viewers(story_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"viewers": viewers}
