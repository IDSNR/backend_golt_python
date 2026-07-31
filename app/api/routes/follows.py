from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_optional_user
from app.services import notification_service, profile_service, social_service

router = APIRouter(prefix="/follows", tags=["follows"])


class FollowRequest(BaseModel):
    followeeProfileId: str


class DecisionResponse(BaseModel):
    status: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_follow_request(payload: FollowRequest, current_user: str = Depends(get_current_user)) -> dict:
    profile = profile_service.ensure_profile(payload.followeeProfileId)
    profile_service.ensure_profile(current_user)
    try:
        request = social_service.follow(current_user, payload.followeeProfileId, followee_is_private=profile.get('isPrivate', False))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if request['status'] == 'approved':
        notification_service.send_notification(
            payload.followeeProfileId,
            'new_follower',
            {
                'followerId': current_user,
                'followRequestId': request['id'],
            },
        )

    return {"status": request['status']}


@router.delete("/{followee_profile_id}")
def unfollow(followee_profile_id: str, current_user: str = Depends(get_current_user)) -> dict:
    social_service.unfollow(current_user, followee_profile_id)
    return {"status": "unfollowed"}


@router.get("/requests")
def list_follow_requests(current_user: str = Depends(get_current_user)) -> dict:
    requests = social_service.list_follow_requests(current_user)
    response = [
        {
            "id": request["id"],
            "follower_profile_id": request["followerId"],
            "followee_profile_id": request["followeeId"],
            "created_at": request["created_at"],
        }
        for request in requests
    ]
    return {"requests": response}


@router.post("/{follower_profile_id}/{decision}")
def decide_follow_request(
    follower_profile_id: str,
    decision: str,
    current_user: str = Depends(get_current_user),
) -> dict:
    if decision not in {"approve", "deny"}:
        raise HTTPException(status_code=400, detail="Invalid decision")

    try:
        if decision == "approve":
            request = social_service.approve_by_follower(current_user, follower_profile_id)
        else:
            request = social_service.deny_by_follower(current_user, follower_profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"status": request["status"]}
