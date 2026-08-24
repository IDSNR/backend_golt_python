from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/referrals", tags=["referrals"])


class ReferralCreateRequest(BaseModel):
    referrerId: str
    inviteeId: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_referral(payload: ReferralCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    invitee_id = current_user
    if payload.referrerId == invitee_id:
        raise HTTPException(status_code=400, detail="referrerId and inviteeId must differ")
    return {"referral": {"id": "referral-1", "referrerId": payload.referrerId, "inviteeId": invitee_id}}
