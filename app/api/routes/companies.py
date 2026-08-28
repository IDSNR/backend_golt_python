from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyCreateRequest(BaseModel):
    name: str
    handle: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    return {"company": {"id": f"company-{payload.handle}", "name": payload.name, "handle": payload.handle, "ownerId": current_user}}
