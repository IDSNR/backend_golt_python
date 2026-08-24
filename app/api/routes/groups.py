from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.modules.groups import GroupService

router = APIRouter(prefix='/groups', tags=['groups'])
group_service = GroupService()


class GroupCreateRequest(BaseModel):
    name: str
    description: str | None = None
    isPrivate: bool = False


@router.get('')
def list_groups() -> dict:
    return {'groups': group_service.list_groups()}


@router.post('', status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        group = group_service.create_group(current_user, payload.name, payload.description, payload.isPrivate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'group': group}


@router.get('/{group_id}')
def get_group(group_id: str) -> dict:
    group = group_service.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail='Group not found')
    return {'group': group, 'members': group_service.list_members(group_id)}


@router.post('/{group_id}/join')
def join_group(group_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        role = group_service.join_group(group_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {'status': role}


@router.delete('/{group_id}/membership')
def leave_group(group_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        group_service.leave_group(group_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400 if 'owner' in str(exc) else 404, detail=str(exc)) from exc
    return {'status': 'left'}


@router.post('/{group_id}/members/{account_id}/approve')
def approve_member(group_id: str, account_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        role = group_service.approve_member(group_id, account_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=403 if 'owner' in str(exc) else 404, detail=str(exc)) from exc
    return {'status': role}
