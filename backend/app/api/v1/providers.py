from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import Provider, User, UserProvider
from app.db.session import get_db
from app.dependencies import get_current_user, get_optional_user
from app.schemas.common import OkResponse
from app.schemas.providers import ConnectRequest, ProviderResponse

router = APIRouter(prefix="/providers", tags=["providers"])


async def _connected_ids(db: AsyncSession, user: User | None) -> set[str]:
    if not user:
        return set()
    rows = (
        (await db.execute(select(UserProvider.provider_id).where(UserProvider.user_id == user.id)))
        .scalars()
        .all()
    )
    return set(rows)


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[ProviderResponse]:
    rows = (
        (
            await db.execute(
                select(Provider).where(Provider.is_active.is_(True)).order_by(Provider.priority)
            )
        )
        .scalars()
        .all()
    )
    connected = await _connected_ids(db, user)
    return [
        ProviderResponse.model_validate(p, from_attributes=True).model_copy(
            update={"connected": p.id in connected}
        )
        for p in rows
    ]


@router.get("/connected", response_model=list[ProviderResponse])
async def connected_providers(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ProviderResponse]:
    rows = (
        (
            await db.execute(
                select(Provider)
                .join(UserProvider, UserProvider.provider_id == Provider.id)
                .where(UserProvider.user_id == user.id)
                .order_by(Provider.priority)
            )
        )
        .scalars()
        .all()
    )
    return [
        ProviderResponse.model_validate(p, from_attributes=True).model_copy(
            update={"connected": True}
        )
        for p in rows
    ]


@router.post("/connect", response_model=OkResponse)
async def connect(
    payload: ConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    prov = (
        await db.execute(select(Provider).where(Provider.id == payload.provider_id))
    ).scalar_one_or_none()
    if not prov:
        raise NotFoundError("Такого сервиса нет.")
    exists = (
        await db.execute(
            select(UserProvider).where(
                UserProvider.user_id == user.id, UserProvider.provider_id == prov.id
            )
        )
    ).scalar_one_or_none()
    if not exists:
        db.add(UserProvider(user_id=user.id, provider_id=prov.id))
        await db.commit()
    return OkResponse()


@router.delete("/disconnect/{provider_id}", response_model=OkResponse)
async def disconnect(
    provider_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> OkResponse:
    await db.execute(
        delete(UserProvider).where(
            UserProvider.user_id == user.id, UserProvider.provider_id == provider_id
        )
    )
    await db.commit()
    return OkResponse()
