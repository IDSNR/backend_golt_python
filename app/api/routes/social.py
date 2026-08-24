from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.modules.social.service import SocialService
from app.api.dependencies import get_current_user
from app.services import social_service

router = APIRouter(prefix="/social", tags=["social"])
service = social_service


class FollowRequest(BaseModel):
    followerId: str
    followeeId: str


class ApproveRequest(BaseModel):
    requestId: str


@router.post("/follow", status_code=status.HTTP_201_CREATED)
def follow(payload: FollowRequest, current_user: str = Depends(get_current_user)) -> dict:
    if payload.followerId != current_user:
        raise HTTPException(status_code=403, detail='followerId must match the authenticated user')
    try:
        request = service.follow(current_user, payload.followeeId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"followRequest": request}


@router.get("/follow-requests/{followee_id}")
def list_follow_requests(followee_id: str, current_user: str = Depends(get_current_user)) -> dict:
    if followee_id != current_user:
        raise HTTPException(status_code=403, detail='Cannot view another user\'s follow requests')
    return {"followRequests": service.list_follow_requests(current_user)}


@router.post("/follow-requests/approve", status_code=status.HTTP_200_OK)
def approve_follow_request(payload: ApproveRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        request = service.approve(payload.requestId, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"followRequest": request}
