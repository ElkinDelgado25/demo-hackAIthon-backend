from pydantic import EmailStr, Field

from app.shared.enums import UserRole
from app.shared.schemas import ApiModel


class UserCreate(ApiModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.AUDITOR


class UserRead(ApiModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
