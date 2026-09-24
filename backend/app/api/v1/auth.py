from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.models import User, UserPreferences
from app.db.session import get_db
from app.dependencies import auth_rate_limit, get_current_user
from app.schemas.auth import (
    LoginRequest,
    PatchMeRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = (
        await db.execute(select(User).where(User.email == str(payload.email).lower()))
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("Пользователь с таким email уже зарегистрирован.")
    if len(payload.password) < 6:
        raise AuthError("Пароль должен быть не короче 6 символов.")
    user = User(
        email=str(payload.email).lower(),
        hashed_password=get_password_hash(payload.password),
        display_name=payload.display_name or str(payload.email).split("@")[0],
    )
    db.add(user)
    await db.flush()
    db.add(UserPreferences(user_id=user.id))
    await db.commit()
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = (
        await db.execute(select(User).where(User.email == str(payload.email).lower()))
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Неверный email или пароль.")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise AuthError("Сессия истекла. Войдите снова.")
    user = (await db.execute(select(User).where(User.id == data.get("sub")))).scalar_one_or_none()
    if not user:
        raise AuthError("Пользователь не найден. Войдите снова.")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserResponse)
async def patch_me(
    payload: PatchMeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if payload.display_name is not None:
        user.display_name = payload.display_name[:120]
    if payload.onboarding_completed is not None:
        user.onboarding_completed = payload.onboarding_completed
    if payload.preferred_theme in ("auto", "light", "dark"):
        user.preferred_theme = payload.preferred_theme  # type: ignore[assignment]
    if payload.preferred_language in ("ru", "en"):
        user.preferred_language = payload.preferred_language  # type: ignore[assignment]
    await db.commit()
    await db.refresh(user)
    return user
