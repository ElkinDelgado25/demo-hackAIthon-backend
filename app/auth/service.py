from app.auth.schemas import LoginRequest, TokenResponse
from app.core.exceptions import AppError
from app.core.security import create_access_token, verify_password
from app.users.service import get_user_by_email, user_to_read


async def authenticate_user(payload: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise AppError("Credenciales invalidas.", status_code=401)
    if not user.is_active:
        raise AppError("Usuario inactivo.", status_code=403)

    token = create_access_token(str(user.id), {"role": user.role.value})
    return TokenResponse(access_token=token, user=user_to_read(user))
