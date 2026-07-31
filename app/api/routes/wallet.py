from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_optional_user
from app.services import wallet_service

router = APIRouter(prefix="/wallet", tags=["wallet"])


class WithdrawalRequest(BaseModel):
    amountCents: int


class BoostPurchaseRequest(BaseModel):
    costCents: int


@router.get("/balance")
def get_balance(current_user: str | None = Depends(get_optional_user)) -> dict:
    user_id = current_user or 'anonymous'
    return {"balanceCents": wallet_service.get_balance(user_id)}


@router.post("/withdraw", status_code=status.HTTP_200_OK)
def withdraw(payload: WithdrawalRequest, current_user: str | None = Depends(get_optional_user)) -> dict:
    user_id = current_user or 'anonymous'
    try:
        new_balance = wallet_service.withdraw(user_id, payload.amountCents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"balanceCents": new_balance}


@router.post("/boost", status_code=status.HTTP_200_OK)
def buy_boost(payload: BoostPurchaseRequest, current_user: str | None = Depends(get_optional_user)) -> dict:
    user_id = current_user or 'anonymous'
    try:
        result = wallet_service.boost_purchase(user_id, payload.costCents)
    except ValueError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    return result
