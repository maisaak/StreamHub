from __future__ import annotations

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Content, UserPreferences, ViewHistory


async def _prefs(db: AsyncSession, user_id: uuid.UUID | None) -> UserPreferences | None:
    if not user_id:
        return None
    return (
        await db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
    ).scalar_one_or_none()


async def _watched_ids(db: AsyncSession, user_id: uuid.UUID | None) -> set[uuid.UUID]:
    if not user_id:
        return set()
    rows = (
        (
            await db.execute(
                select(ViewHistory.content_id).where(
                    ViewHistory.user_id == user_id, ViewHistory.watched.is_(True)
                )
            )
        )
        .scalars()
        .all()
    )
    return set(rows)


async def recommend(db: AsyncSession, user_id: uuid.UUID | None, limit: int = 12) -> list[Content]:
    prefs = await _prefs(db, user_id)
    genres = [g.lower() for g in (prefs.favorite_genres if prefs else [])]
    hide_watched = bool(prefs and prefs.hide_watched)
    watched = await _watched_ids(db, user_id) if hide_watched else set()

    rows = (
        (
            await db.execute(
                select(Content)
                .options(selectinload(Content.sources))
                .order_by(desc(Content.popularity))
                .limit(60)
            )
        )
        .scalars()
        .all()
    )

    def score(c: Content) -> float:
        s = float(c.popularity or 0)
        cg = [(g or "").lower() for g in (c.genres or [])]
        overlap = len(set(cg) & set(genres))
        s += overlap * 25
        if c.rating_kinopoisk:
            s += float(c.rating_kinopoisk)
        return s

    ranked = sorted(rows, key=score, reverse=True)
    out = [c for c in ranked if c.id not in watched][:limit]
    return out


async def continue_watching(db: AsyncSession, user_id: uuid.UUID, limit: int = 12) -> list[Content]:
    rows = (
        (
            await db.execute(
                select(ViewHistory)
                .where(ViewHistory.user_id == user_id, ViewHistory.watched.is_(False))
                .order_by(desc(ViewHistory.viewed_at))
                .limit(limit * 2)
            )
        )
        .scalars()
        .all()
    )
    seen: set[uuid.UUID] = set()
    cids: list[uuid.UUID] = []
    for r in rows:
        if r.content_id not in seen:
            seen.add(r.content_id)
            cids.append(r.content_id)
    if not cids:
        return []
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
    return [by_id[i] for i in cids if i in by_id][:limit]


async def popular(
    db: AsyncSession, limit: int = 12, exclude: set[uuid.UUID] | None = None
) -> list[Content]:
    q = (
        select(Content)
        .options(selectinload(Content.sources))
        .order_by(desc(Content.popularity))
        .limit(limit * 2)
    )
    rows = (await db.execute(q)).scalars().all()
    ex = exclude or set()
    return [c for c in rows if c.id not in ex][:limit]
