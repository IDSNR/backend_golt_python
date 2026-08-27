from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_optional_user
from app.services import notification_service, push_notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])
service = notification_service


class PushTokenRequest(BaseModel):
    token: str
    platform: Literal["android", "ios"]


@router.post("/push-tokens", status_code=status.HTTP_201_CREATED)
def register_push_token(payload: PushTokenRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        registration = push_notification_service.register(current_user, payload.token, payload.platform)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"registration": registration}


@router.delete("/push-tokens")
def unregister_push_token(payload: PushTokenRequest, current_user: str = Depends(get_current_user)) -> dict:
    push_notification_service.unregister(current_user, payload.token)
    return {"removed": True}


@router.get("")
def list_notifications(current_user: str | None = Depends(get_optional_user)) -> dict:
    if current_user is None:
        return {"notifications": [], "unreadCount": 0}
    notifications = service.list_for_recipient(current_user)
    unread_count = service.count_unread(current_user)
    return {"notifications": notifications, "unreadCount": unread_count}


@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        service.mark_read(notification_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"read": True}
