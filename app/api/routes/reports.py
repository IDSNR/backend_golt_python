from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportCreateRequest(BaseModel):
    targetType: str
    targetId: str
    reason: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    if not payload.reason.strip():
        raise HTTPException(status_code=400, detail="reason is required")
    return {"report": {"id": "report-1", "reporterId": current_user, "targetType": payload.targetType, "targetId": payload.targetId, "reason": payload.reason}}
