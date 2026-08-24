from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_optional_user
from app.services import content_service, profile_service

router = APIRouter(prefix="/search", tags=["search"])


class SearchQuery(BaseModel):
    query: str


@router.get("")
def search(query: str, current_user: str | None = Depends(get_optional_user)) -> dict:
    query_lower = query.strip().lower()
    profiles = [
        profile for profile in profile_service.profiles.values()
        if query_lower in profile.get('handle', '').lower() or query_lower in (profile.get('displayName') or '').lower()
    ]
    posts = [
        post for post in content_service.list_public_posts()
        if query_lower in (post.get('caption') or '').lower()
    ]
    return {
        'profiles': profiles,
        'posts': posts,
    }
