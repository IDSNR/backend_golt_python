from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user

from app.modules.commerce.service import CommerceService

router = APIRouter(prefix="/purchases", tags=["purchases"])
service = CommerceService()


class PurchaseCreateRequest(BaseModel):
    contentId: str
    amountCents: int = 0


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase(payload: PurchaseCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    purchase = service.create_purchase(current_user, payload.model_dump())
    return {"purchase": purchase}
