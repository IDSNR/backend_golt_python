from fastapi import Header, HTTPException


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    if authorization:
        if authorization.lower().startswith('bearer '):
            token = authorization[7:].strip()
            if token:
                return token
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
            return token or None
        raise HTTPException(status_code=401, detail='Invalid Authorization header')

    if x_user_id:
        return x_user_id

    return None
