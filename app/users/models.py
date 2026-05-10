from datetime import datetime

from beanie import Document, Indexed
from pydantic import EmailStr, Field

from app.shared.enums import UserRole
from app.shared.schemas import utc_now


class User(Document):
    email: Indexed(EmailStr, unique=True)
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.AUDITOR
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "users"
