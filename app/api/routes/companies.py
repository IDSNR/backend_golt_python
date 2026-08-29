from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    handle: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    handle = payload.handle.lower()
    return {"company": {"id": f"company-{handle}", "name": payload.name.strip(), "handle": handle, "ownerId": current_user}}
