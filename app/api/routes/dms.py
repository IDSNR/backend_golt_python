from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services import direct_message_service, profile_service

router = APIRouter(prefix="/dms", tags=["dms"])


class CreateThreadRequest(BaseModel):
    recipientId: str
    initialMessage: str


class SendMessageRequest(BaseModel):
    content: str


@router.get("")
def list_threads(current_user: str = Depends(get_current_user)) -> dict:
    threads = direct_message_service.list_threads(current_user)
    return {'threads': threads}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_thread(payload: CreateThreadRequest, current_user: str = Depends(get_current_user)) -> dict:
    if current_user == payload.recipientId:
        raise HTTPException(status_code=400, detail='Cannot message yourself')
    recipient = profile_service.get_profile(payload.recipientId)
    if recipient is None:
        raise HTTPException(status_code=404, detail='Recipient not found')
    thread = direct_message_service.create_thread(current_user, payload.recipientId, payload.initialMessage)
    return {'thread': thread}


@router.get("/{thread_id}")
def get_thread(thread_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        thread = direct_message_service.get_thread(thread_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {'thread': thread}


@router.post("/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(thread_id: str, payload: SendMessageRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        message = direct_message_service.send_message(thread_id, current_user, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {'message': message}
