from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Content, SearchHistory, User, UserProvider
from app.db.session import get_db
from app.dependencies import get_current_user, get_optional_user, search_rate_limit
from app.schemas.common import OkResponse
from app.schemas.search import HistoryItem, SearchResponse, SuggestItem, SuggestResponse
from app.services.aggregator_service import catalog_suggestions, unified_search
from app.services.history_service import record_search
from app.services.matcher_service import gated_fuzzy_score

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(search_rate_limit)])


async def _connected(db: AsyncSession, user: User | None) -> set[str]:
    if not user:
        return set()
    rows = (
        (await db.execute(select(UserProvider.provider_id).where(UserProvider.user_id == user.id)))
        .scalars()
        .all()
    )
    return set(rows)


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(default="", max_length=500),
    type: str | None = Query(default=None, pattern="^(movie|series|video)$"),  # noqa: A002
    year: int | None = Query(default=None, ge=1900, le=2030),
    only_my: bool = False,
    free: bool = False,
    quality: str | None = Query(default=None, pattern="^(any|SD|HD|4K)$"),
    genres: str | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> SearchResponse:
    connected = await _connected(db, user)
    genre_list = [g.strip() for g in genres.split(",") if g.strip()] if genres else None
    items, partial, failed, took_ms = await unified_search(
        db,
        q,
        ctype=type,
        year=year,
        connected=connected,
        only_my=only_my,
        free_only=free,
        quality=quality,
        genres=genre_list,
        min_rating=min_rating,
    )
    suggestions: list[str] = []
    if not items and q.strip():
        suggestions = await catalog_suggestions(db, q)
    if user and q.strip():
        await record_search(db, user.id, q)
    return SearchResponse(
        items=items,
        total=len(items),
        partial=partial,
        failed_providers=failed,
        suggestions=suggestions,
        took_ms=took_ms,
    )


@router.get("/suggest", response_model=SuggestResponse)
async def suggest(
    q: str = Query(default="", max_length=200),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> SuggestResponse:
    q = q.strip()
    items: list[SuggestItem] = []
    # 1. user history matches first (icon 🕓 on frontend)
    if user and q:
        rows = (
            (
                await db.execute(
                    select(SearchHistory.query)
                    .where(SearchHistory.user_id == user.id, SearchHistory.query.ilike(f"%{q}%"))
                    .order_by(desc(SearchHistory.searched_at))
                    .limit(20)
                )
            )
            .scalars()
            .all()
        )
        seen: set[str] = set()
        for query in rows:
            if query.lower() not in seen:
                seen.add(query.lower())
                items.append(SuggestItem(kind="history", text=query))
            if len(items) >= 3:
                break
    # 2. catalog matches with posters
    if q:
        contents = (
            (await db.execute(select(Content).options(selectinload(Content.sources)).limit(300)))
            .scalars()
            .all()
        )
        scored = sorted(
            ((gated_fuzzy_score(q, c.title), c) for c in contents),
            key=lambda x: -x[0],
        )
        nq = q.lower()
        for score, c in scored:
            titles_l = f"{c.title} {c.original_title}".lower()
            if nq in titles_l:
                pass
            elif len(nq) < 4 or score < 60:
                continue
            items.append(
                SuggestItem(
                    kind="content",
                    text=c.title,
                    content_id=str(c.id),
                    poster_url=c.poster_url or "",
                    year=c.year,
                )
            )
            if len(items) >= 7:
                break
    return SuggestResponse(items=items[:7])


@router.get("/history", response_model=list[HistoryItem])
async def get_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[HistoryItem]:
    rows = (
        (
            await db.execute(
                select(SearchHistory)
                .where(SearchHistory.user_id == user.id)
                .order_by(desc(SearchHistory.searched_at))
                .limit(20)
            )
        )
        .scalars()
        .all()
    )
    return [
        HistoryItem(id=r.id, query=r.query, searched_at=r.searched_at.isoformat()) for r in rows
    ]


@router.delete("/history", response_model=OkResponse)
async def clear_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> OkResponse:
    await db.execute(delete(SearchHistory).where(SearchHistory.user_id == user.id))
    await db.commit()
    return OkResponse()
