from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.services import wallet_service

router = APIRouter(prefix="/wallet", tags=["wallet"])


class WithdrawalRequest(BaseModel):
    amountCents: int = Field(gt=0)


class BoostPurchaseRequest(BaseModel):
    costCents: int = Field(gt=0)


@router.get("/balance")
def get_balance(current_user: str = Depends(get_current_user)) -> dict:
    return {"balanceCents": wallet_service.get_balance(current_user)}


@router.post("/withdraw", status_code=status.HTTP_200_OK)
def withdraw(payload: WithdrawalRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        new_balance = wallet_service.withdraw(current_user, payload.amountCents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"balanceCents": new_balance}


@router.post("/boost", status_code=status.HTTP_200_OK)
def buy_boost(payload: BoostPurchaseRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        result = wallet_service.boost_purchase(current_user, payload.costCents)
    except ValueError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return result
