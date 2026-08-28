from fastapi import Header, HTTPException

from app.modules.auth.service import auth_service


def get_current_user(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='Bearer session required')
    user_id = auth_service.validate_session(authorization[7:].strip())
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid or expired session')
    return user_id


def get_optional_user(
    authorization: str | None = Header(default=None),
) -> str | None:
    if not authorization:
        return None
    if not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='Invalid Authorization header')
    user_id = auth_service.validate_session(authorization[7:].strip())
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid or expired session')
    return user_id
