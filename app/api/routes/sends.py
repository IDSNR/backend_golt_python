from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/sends", tags=["sends"])


class SendCreateRequest(BaseModel):
    senderId: str
    recipientId: str
    amountCents: int


@router.post("", status_code=status.HTTP_201_CREATED)
def create_send(payload: SendCreateRequest) -> dict:
    if payload.amountCents < 0:
        raise HTTPException(status_code=400, detail="amountCents must be a non-negative integer")
    return {"send": {"id": "send-1", "senderId": payload.senderId, "recipientId": payload.recipientId, "amountCents": payload.amountCents}}
