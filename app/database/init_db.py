from app.core.config import settings
from app.core.security import get_password_hash
from app.shared.enums import UserRole
from app.users.models import User


async def ensure_default_admin() -> None:
    existing = await User.find_one(User.email == settings.default_admin_email)
    if existing:
        return

    user = User(
        email=settings.default_admin_email,
        full_name=settings.default_admin_full_name,
        hashed_password=get_password_hash(settings.default_admin_password),
        role=UserRole.ADMIN,
    )
    await user.insert()
