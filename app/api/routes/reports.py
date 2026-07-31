from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportCreateRequest(BaseModel):
    targetType: str
    targetId: str
    reason: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreateRequest) -> dict:
    if not payload.reason.strip():
        raise HTTPException(status_code=400, detail="reason is required")
    return {"report": {"id": "report-1", "targetType": payload.targetType, "targetId": payload.targetId, "reason": payload.reason}}
