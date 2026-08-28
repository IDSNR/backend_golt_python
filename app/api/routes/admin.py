from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.modules.moderation.service import list_queue, require_admin, update_report

router = APIRouter(prefix='/admin', tags=['admin'])


class ModerationDecision(BaseModel):
    status: str
    notes: str | None = None


@router.get('/moderation/queue')
def moderation_queue(
    queue_status: str = Query(default='open', alias='status'),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: str = Depends(get_current_user),
) -> dict:
    try:
        require_admin(current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return {'reports': list_queue(queue_status, limit)}


@router.patch('/moderation/{report_id}')
def decide_report(
    report_id: str,
    payload: ModerationDecision,
    current_user: str = Depends(get_current_user),
) -> dict:
    if payload.status not in {'open', 'reviewing', 'resolved', 'dismissed'}:
        raise HTTPException(status_code=400, detail='invalid moderation status')
    try:
        require_admin(current_user)
        report = update_report(report_id, payload.status, current_user, payload.notes)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {'report': report}
