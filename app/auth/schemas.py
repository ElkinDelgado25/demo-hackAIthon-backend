from pydantic import EmailStr, Field

from app.shared.schemas import ApiModel
from app.users.schemas import UserRead


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(ApiModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
