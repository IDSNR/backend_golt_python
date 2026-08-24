from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.modules.auth.service import auth_service
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    displayName: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    email: str
    displayName: str | None = None
    googleId: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    try:
        return auth_service.register_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.displayName or "New user",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login")
def login(payload: LoginRequest):
    try:
        return auth_service.authenticate_user(email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/google")
def google_auth(payload: GoogleAuthRequest):
    return auth_service.handle_google_auth(
        email=payload.email,
        display_name=payload.displayName or "Google user",
        google_id=payload.googleId,
    )


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), current_user: str = Depends(get_current_user)) -> dict:
    if authorization and authorization.lower().startswith('bearer '):
        auth_service.revoke_session(authorization[7:].strip())
    return {"loggedOut": True, "userId": current_user}
