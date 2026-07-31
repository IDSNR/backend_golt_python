from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyCreateRequest(BaseModel):
    name: str
    handle: str


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreateRequest, x_user_id: str | None = Header(default=None)) -> dict:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return {"company": {"id": f"company-{payload.handle}", "name": payload.name, "handle": payload.handle, "ownerId": x_user_id}}
