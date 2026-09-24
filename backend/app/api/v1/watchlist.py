from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.db.models import Content, User, UserProvider, Watchlist
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import OkResponse
from app.schemas.watchlist import WatchlistAdd, WatchlistItem
from app.services.aggregator_service import content_to_card
from app.services.availability_service import _provider_map

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItem])
async def list_watchlist(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[WatchlistItem]:
    rows = (
        (
            await db.execute(
                select(Watchlist)
                .where(Watchlist.user_id == user.id)
                .order_by(desc(Watchlist.added_at))
                .limit(200)
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return []
    cids = [r.content_id for r in rows]
    contents = (
        (
            await db.execute(
                select(Content).where(Content.id.in_(cids)).options(selectinload(Content.sources))
            )
        )
        .scalars()
        .all()
    )
    by_id = {c.id: c for c in contents}
    prov_ids = (
        (await db.execute(select(UserProvider.provider_id).where(UserProvider.user_id == user.id)))
        .scalars()
        .all()
    )
    providers = await _provider_map(db)
    connected = set(prov_ids)
    out: list[WatchlistItem] = []
    for r in rows:
        c = by_id.get(r.content_id)
        if c:
            out.append(
                WatchlistItem(
                    id=r.id,
                    added_at=r.added_at.isoformat(),
                    notify_on_release=r.notify_on_release,
                    content=content_to_card(c, providers, connected),
                )
            )
    return out


@router.post("", response_model=OkResponse)
async def add_watchlist(
    payload: WatchlistAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    try:
        cid = uuid.UUID(payload.content_id)
    except ValueError as e:
        raise NotFoundError("Контент не найден.") from e
    content = (await db.execute(select(Content).where(Content.id == cid))).scalar_one_or_none()
    if not content:
        raise NotFoundError("Контент не найден.")
    exists = (
        await db.execute(
            select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.content_id == cid)
        )
    ).scalar_one_or_none()
    if not exists:
        db.add(
            Watchlist(user_id=user.id, content_id=cid, notify_on_release=payload.notify_on_release)
        )
        await db.commit()
    return OkResponse()


@router.delete("/{item_id}", response_model=OkResponse)
async def remove_watchlist(
    item_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> OkResponse:
    await db.execute(delete(Watchlist).where(Watchlist.id == item_id, Watchlist.user_id == user.id))
    await db.commit()
    return OkResponse()


@router.delete("/by-content/{content_id}", response_model=OkResponse)
async def remove_by_content(
    content_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    await db.execute(
        delete(Watchlist).where(Watchlist.content_id == content_id, Watchlist.user_id == user.id)
    )
    await db.commit()
    return OkResponse()
