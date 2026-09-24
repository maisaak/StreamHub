from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SearchHistory, ViewHistory

SEARCH_HISTORY_LIMIT = 100


async def record_search(db: AsyncSession, user_id: uuid.UUID, query: str) -> None:
    q = query.strip()
    if not q:
        return
    db.add(SearchHistory(user_id=user_id, query=q[:500]))
    await db.commit()
    # prune to last 100
    ids = (
        (
            await db.execute(
                select(SearchHistory.id)
                .where(SearchHistory.user_id == user_id)
                .order_by(desc(SearchHistory.searched_at), desc(SearchHistory.id))
                .offset(SEARCH_HISTORY_LIMIT)
            )
        )
        .scalars()
        .all()
    )
    if ids:
        await db.execute(delete(SearchHistory).where(SearchHistory.id.in_(ids)))
        await db.commit()


async def record_view(
    db: AsyncSession,
    user_id: uuid.UUID,
    content_id: uuid.UUID,
    provider_id: str | None = None,
    watched: bool = False,
) -> None:
    # upsert-ish: update existing row's timestamp if same content+provider recently
    existing = (
        await db.execute(
            select(ViewHistory).where(
                ViewHistory.user_id == user_id,
                ViewHistory.content_id == content_id,
                ViewHistory.provider_id == provider_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.viewed_at = datetime.now(UTC)
        if watched:
            existing.watched = True
    else:
        db.add(
            ViewHistory(
                user_id=user_id, content_id=content_id, provider_id=provider_id, watched=watched
            )
        )
    await db.commit()


async def search_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    return int(
        (await db.execute(select(func.count()).where(SearchHistory.user_id == user_id))).scalar()
        or 0
    )
