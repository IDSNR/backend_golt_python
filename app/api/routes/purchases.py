from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.services import commerce_service

router = APIRouter(prefix="/purchases", tags=["purchases"])
service = commerce_service


class PurchaseCreateRequest(BaseModel):
    contentId: str
    amountCents: int = Field(gt=0)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_purchase(payload: PurchaseCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    purchase = service.create_purchase(current_user, payload.model_dump())
    return {"purchase": purchase}
