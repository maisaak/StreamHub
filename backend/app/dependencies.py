from __future__ import annotations

import uuid

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, RateLimitError
from app.core.redis import get_redis
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    payload = decode_token(authorization.split(" ", 1)[1].strip())
    if not payload or payload.get("type") != "access":
        return None
    try:
        uid = uuid.UUID(str(payload.get("sub")))
    except ValueError:
        return None
    return (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()


async def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise AuthError()
    return user


async def rate_limit(request: Request, key: str, limit: int, window_seconds: int) -> None:
    redis = await get_redis()
    rkey = f"rl:{key}"
    try:
        count = await redis.incr(rkey)
        if count == 1:
            await redis.expire(rkey, window_seconds)
        if count > limit:
            raise RateLimitError()
    except RateLimitError:
        raise
    except Exception:
        return  # fail-open if redis unavailable


async def search_rate_limit(
    request: Request, user: User | None = Depends(get_optional_user)
) -> None:
    ident = str(user.id) if user else (request.client.host if request.client else "anon")
    await rate_limit(request, f"search:{ident}", 30, 60)


async def auth_rate_limit(request: Request) -> None:
    ident = request.client.host if request.client else "anon"
    await rate_limit(request, f"auth:{ident}", 10, 900)
