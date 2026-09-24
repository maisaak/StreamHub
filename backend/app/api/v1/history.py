from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Content, User, UserProvider, ViewHistory
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.common import OkResponse
from app.schemas.history import ViewHistoryItem
from app.services.aggregator_service import content_to_card
from app.services.availability_service import _provider_map

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[ViewHistoryItem])
async def list_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ViewHistoryItem]:
    rows = (
        (
            await db.execute(
                select(ViewHistory)
                .where(ViewHistory.user_id == user.id)
                .order_by(desc(ViewHistory.viewed_at))
                .limit(100)
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return []
    cids = list({r.content_id for r in rows})
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
    return [
        ViewHistoryItem(
            id=r.id,
            viewed_at=r.viewed_at.isoformat(),
            provider_id=r.provider_id,
            watched=r.watched,
            content=content_to_card(by_id[r.content_id], providers, connected),
        )
        for r in rows
        if r.content_id in by_id
    ]


@router.delete("", response_model=OkResponse)
async def clear_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> OkResponse:
    await db.execute(delete(ViewHistory).where(ViewHistory.user_id == user.id))
    await db.commit()
    return OkResponse()
