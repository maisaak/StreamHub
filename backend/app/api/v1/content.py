from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import NotFoundError
from app.db.models import Content, ShortLink, User, UserProvider
from app.db.session import get_db
from app.dependencies import get_current_user, get_optional_user
from app.schemas.content import (
    AvailabilityResponse,
    ContentCard,
    ContentDetail,
    FeedSection,
    HomeFeed,
    ShortLinkResponse,
    SimilarResponse,
)
from app.schemas.history import MarkWatchedRequest
from app.services.aggregator_service import content_to_card, similar_content
from app.services.availability_service import _provider_map, get_availability
from app.services.history_service import record_view
from app.services.recommendation_service import continue_watching, popular, recommend

router = APIRouter(prefix="/content", tags=["content"])


async def _connected(db: AsyncSession, user: User | None) -> set[str]:
    if not user:
        return set()
    rows = (
        (await db.execute(select(UserProvider.provider_id).where(UserProvider.user_id == user.id)))
        .scalars()
        .all()
    )
    return set(rows)


def _short_for(content_id: uuid.UUID) -> str:
    return f"{settings.SHORT_LINK_BASE}/s/{content_id.hex[:8]}"


@router.get("/feed", response_model=HomeFeed)
async def home_feed(
    db: AsyncSession = Depends(get_db), user: User | None = Depends(get_optional_user)
) -> HomeFeed:
    connected = await _connected(db, user)
    providers = await _provider_map(db)
    sections: list[FeedSection] = []
    used: set[uuid.UUID] = set()

    def cards(contents: list[Content]) -> list[ContentCard]:
        out = []
        for c in contents:
            if c.id in used:
                continue
            used.add(c.id)
            out.append(content_to_card(c, providers, connected))
        return out

    # 1. Continue watching
    if user:
        cw = await continue_watching(db, user.id)
        items = cards(cw)
        if items:
            sections.append(FeedSection(key="continue", title="Продолжить просмотр", items=items))

    # 2. From my subscriptions
    if connected:
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
        mine = [c for c in rows if {s.provider_id for s in c.sources} & connected]
        items = cards(mine[:12])
        if items:
            sections.append(FeedSection(key="mine", title="Из ваших подписок", items=items))

    # 3. Popular
    pop = await popular(db, limit=12, exclude=used)
    items = cards(pop)
    if items:
        sections.append(FeedSection(key="popular", title="Популярное за неделю", items=items))

    # 4. Recommended
    rec = await recommend(db, user.id if user else None, limit=24)
    items = cards(rec)
    if items:
        sections.append(FeedSection(key="recommended", title="Рекомендуем вам", items=items))

    return HomeFeed(sections=sections)


@router.get("/popular", response_model=list[ContentCard])
async def popular_list(
    db: AsyncSession = Depends(get_db), user: User | None = Depends(get_optional_user)
) -> list[ContentCard]:
    connected = await _connected(db, user)
    providers = await _provider_map(db)
    rows = await popular(db, limit=24)
    return [content_to_card(c, providers, connected) for c in rows]


@router.get("/{content_id}", response_model=ContentDetail)
async def get_content(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> ContentDetail:
    content = (
        await db.execute(
            select(Content).where(Content.id == content_id).options(selectinload(Content.sources))
        )
    ).scalar_one_or_none()
    if content is None:
        raise NotFoundError("Контент не найден. Возможно, он был удалён.")
    connected = await _connected(db, user)
    providers = await _provider_map(db)
    card = content_to_card(content, providers, connected)
    sources, _best, _partial = await get_availability(db, content.id, connected)
    return ContentDetail(
        **card.model_dump(),
        description=content.description or "",
        sources=sources,
        short_link=_short_for(content.id),
    )


@router.get("/{content_id}/availability", response_model=AvailabilityResponse)
async def availability(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> AvailabilityResponse:
    content = (
        await db.execute(select(Content).where(Content.id == content_id))
    ).scalar_one_or_none()
    if content is None:
        raise NotFoundError("Контент не найден.")
    connected = await _connected(db, user)
    sources, best, partial = await get_availability(db, content.id, connected)
    return AvailabilityResponse(
        content_id=content.id, sources=sources, best_source=best, partial=partial
    )


@router.get("/{content_id}/similar", response_model=SimilarResponse)
async def similar(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> SimilarResponse:
    connected = await _connected(db, user)
    items = await similar_content(db, content_id, connected)
    return SimilarResponse(items=items)


@router.post("/{content_id}/mark-watched")
async def mark_watched(
    content_id: uuid.UUID,
    payload: MarkWatchedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    content = (
        await db.execute(select(Content).where(Content.id == content_id))
    ).scalar_one_or_none()
    if content is None:
        raise NotFoundError("Контент не найден.")
    await record_view(db, user.id, content.id, payload.provider_id, watched=payload.watched)
    return {"ok": True}


@router.post("/{content_id}/watch")
async def track_watch(
    content_id: uuid.UUID,
    payload: MarkWatchedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Called on 'Смотреть' click: history + toast on frontend."""
    content = (
        await db.execute(select(Content).where(Content.id == content_id))
    ).scalar_one_or_none()
    if content is None:
        raise NotFoundError("Контент не найден.")
    await record_view(db, user.id, content.id, payload.provider_id, watched=False)
    return {"ok": True}


@router.post("/{content_id}/share", response_model=ShortLinkResponse)
async def share(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> ShortLinkResponse:
    content = (
        await db.execute(select(Content).where(Content.id == content_id))
    ).scalar_one_or_none()
    if content is None:
        raise NotFoundError("Контент не найден.")
    slug = content_id.hex[:8]
    exists = (
        await db.execute(select(ShortLink).where(ShortLink.slug == slug))
    ).scalar_one_or_none()
    if not exists:
        db.add(ShortLink(slug=slug, content_id=content.id))
        await db.commit()
    else:
        slug = exists.slug
    return ShortLinkResponse(short_link=f"{settings.SHORT_LINK_BASE}/s/{slug}", slug=slug)
