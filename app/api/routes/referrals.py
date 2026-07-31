from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/referrals", tags=["referrals"])


class ReferralCreateRequest(BaseModel):
    referrerId: str
    inviteeId: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_referral(payload: ReferralCreateRequest) -> dict:
    if payload.referrerId == payload.inviteeId:
        raise HTTPException(status_code=400, detail="referrerId and inviteeId must differ")
    return {"referral": {"id": "referral-1", "referrerId": payload.referrerId, "inviteeId": payload.inviteeId}}
