from typing import Annotated

from fastapi import Depends, Header

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.users.models import User


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User | None:
    if not authorization:
        if settings.auth_required:
            raise AppError("No autenticado.", status_code=401)
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppError("Formato de autenticacion invalido.", status_code=401)

    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise AppError(str(exc), status_code=401) from exc

    user_id = payload.get("sub")
    user = await User.get(user_id) if user_id else None
    if not user or not user.is_active:
        raise AppError("Usuario no autorizado.", status_code=401)
    return user


CurrentUser = Annotated[User | None, Depends(get_current_user)]
