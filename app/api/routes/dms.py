from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services import (
    direct_message_service,
    notification_service,
    profile_service,
    push_notification_service,
    realtime_service,
)

router = APIRouter(prefix="/dms", tags=["dms"])


class CreateThreadRequest(BaseModel):
    recipientId: str
    initialMessage: str


class SendMessageRequest(BaseModel):
    content: str


async def announce_message(thread: dict, message: dict, sender_id: str, background_tasks: BackgroundTasks) -> None:
    event = {"type": "direct_message", "threadId": thread["id"], "message": message}
    recipients = [participant_id for participant_id in thread["participantIds"] if participant_id != sender_id]

    for recipient_id in recipients:
        notification_service.send_notification(recipient_id, "direct_message", event)
        background_tasks.add_task(
            push_notification_service.send_to_user,
            recipient_id,
            "New message",
            message["content"],
            {"type": "direct_message", "threadId": thread["id"], "messageId": message["id"]},
        )

    await realtime_service.send_to_users(recipients, event)


@router.get("")
def list_threads(current_user: str = Depends(get_current_user)) -> dict:
    threads = direct_message_service.list_threads(current_user)
    return {'threads': threads}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: CreateThreadRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
) -> dict:
    if current_user == payload.recipientId:
        raise HTTPException(status_code=400, detail='Cannot message yourself')
    recipient = profile_service.get_profile(payload.recipientId)
    if recipient is None:
        raise HTTPException(status_code=404, detail='Recipient not found')
    thread = direct_message_service.create_thread(current_user, payload.recipientId, payload.initialMessage)
    thread_detail = direct_message_service.get_thread(thread["id"], current_user)
    await announce_message(thread_detail, thread_detail["messages"][-1], current_user, background_tasks)
    return {'thread': thread}


@router.get("/{thread_id}")
def get_thread(thread_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        thread = direct_message_service.get_thread(thread_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {'thread': thread}


@router.post("/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    thread_id: str,
    payload: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
) -> dict:
    try:
        message = direct_message_service.send_message(thread_id, current_user, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    thread = direct_message_service.get_thread(thread_id, current_user)
    await announce_message(thread, message, current_user, background_tasks)
    return {'message': message}
