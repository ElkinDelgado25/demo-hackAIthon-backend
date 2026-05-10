from fastapi import APIRouter

from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.service import authenticate_user
from app.core.dependencies import CurrentUser
from app.users.schemas import UserCreate, UserRead
from app.users.service import create_user, user_to_read

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(payload: UserCreate) -> UserRead:
    user = await create_user(payload)
    return user_to_read(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    return await authenticate_user(payload)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    if current_user is None:
        return UserRead(id="", email="admin@example.com", full_name="Modo desarrollo", role="ADMIN", is_active=True)
    return user_to_read(current_user)
