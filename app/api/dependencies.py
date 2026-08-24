import os

from fastapi import Header, HTTPException

from app.modules.auth.service import auth_service


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    if authorization:
        if authorization.lower().startswith('bearer '):
            token = authorization[7:].strip()
            user_id = auth_service.validate_session(token)
            if user_id:
                return user_id
            if os.getenv('APP_ENV', 'development').lower() != 'production' and token.startswith(('user-', 'google-', 'engagement-')):
                return token
            raise HTTPException(status_code=401, detail='Invalid or expired session')
        raise HTTPException(status_code=401, detail='Invalid Authorization header')

    if x_user_id:
        return x_user_id

    raise HTTPException(status_code=401, detail='Missing X-User-Id header')


def get_optional_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str | None:
    if authorization:
        if authorization.lower().startswith('bearer '):
            token = authorization[7:].strip()
            user_id = auth_service.validate_session(token)
            if user_id:
                return user_id
            if os.getenv('APP_ENV', 'development').lower() != 'production' and token.startswith(('user-', 'google-', 'engagement-')):
                return token
            raise HTTPException(status_code=401, detail='Invalid or expired session')
        raise HTTPException(status_code=401, detail='Invalid Authorization header')

    if x_user_id:
        return x_user_id

    return None
