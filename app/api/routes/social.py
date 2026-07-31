from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.modules.social.service import SocialService

router = APIRouter(prefix="/social", tags=["social"])
service = SocialService()


class FollowRequest(BaseModel):
    followerId: str
    followeeId: str


class ApproveRequest(BaseModel):
    requestId: str


@router.post("/follow", status_code=status.HTTP_201_CREATED)
def follow(payload: FollowRequest) -> dict:
    try:
        request = service.follow(payload.followerId, payload.followeeId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"followRequest": request}


@router.get("/follow-requests/{followee_id}")
def list_follow_requests(followee_id: str) -> dict:
    return {"followRequests": service.list_follow_requests(followee_id)}


@router.post("/follow-requests/approve", status_code=status.HTTP_200_OK)
def approve_follow_request(payload: ApproveRequest) -> dict:
    try:
        request = service.approve(payload.requestId)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"followRequest": request}
