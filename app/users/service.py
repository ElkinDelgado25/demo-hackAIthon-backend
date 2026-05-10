from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import get_password_hash
from app.shared.schemas import public_id, utc_now
from app.users.models import User
from app.users.schemas import UserCreate, UserRead


def user_to_read(user: User) -> UserRead:
    return UserRead(
        id=public_id(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )


async def create_user(payload: UserCreate) -> User:
    existing = await User.find_one(User.email == payload.email)
    if existing:
        raise ConflictError("Ya existe un usuario con ese email.")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        updated_at=utc_now(),
    )
    await user.insert()
    return user


async def get_user_by_email(email: str) -> User | None:
    return await User.find_one(User.email == email)


async def get_user_or_404(user_id: str) -> User:
    user = await User.get(user_id)
    if not user:
        raise NotFoundError("Usuario no encontrado.")
    return user
