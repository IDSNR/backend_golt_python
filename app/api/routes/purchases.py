from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.modules.commerce.service import CommerceService

router = APIRouter(prefix="/purchases", tags=["purchases"])
service = CommerceService()


class PurchaseCreateRequest(BaseModel):
    contentId: str
    amountCents: int = 0


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase(payload: PurchaseCreateRequest, x_user_id: str | None = Header(default=None)) -> dict:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    purchase = service.create_purchase(x_user_id, payload.model_dump())
    return {"purchase": purchase}
