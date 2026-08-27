from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user

router = APIRouter(prefix="/sends", tags=["sends"])


class SendCreateRequest(BaseModel):
    senderId: str | None = None
    recipientId: str = Field(min_length=1)
    amountCents: int = Field(ge=0)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_send(payload: SendCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    return {"send": {"id": "send-1", "senderId": current_user, "recipientId": payload.recipientId, "amountCents": payload.amountCents}}
