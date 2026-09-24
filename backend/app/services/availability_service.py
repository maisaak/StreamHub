from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Content, ContentSource, Provider
from app.schemas.content import SourceResponse
from app.services.ranking_service import RankInput, rank_key


async def _provider_map(db: AsyncSession) -> dict[str, Provider]:
    rows = (await db.execute(select(Provider))).scalars().all()
    return {p.id: p for p in rows}


def sources_to_response(
    sources: list[ContentSource],
    providers: dict[str, Provider],
    connected: set[str],
) -> tuple[list[SourceResponse], SourceResponse | None]:
    items: list[SourceResponse] = []
    for s in sources:
        p = providers.get(s.provider_id)
        items.append(
            SourceResponse(
                provider_id=s.provider_id,
                provider_name=p.name if p else s.provider_id,
                brand_color=p.brand_color if p else "#000000",
                logo_url=p.logo_url if p else "",
                external_url=s.external_url,
                deep_link=s.deep_link,
                price=s.price,
                is_subscription=s.is_subscription,
                quality=s.quality,
                connected=s.provider_id in connected,
            )
        )

    # rank
    def _key(x: SourceResponse) -> tuple[int, int, float]:
        return rank_key(
            RankInput(x.provider_id, x.connected, x.is_subscription, x.price, x.quality)
        )

    items.sort(key=_key)
    for i, it in enumerate(items):
        it.rank = i
    return items, (items[0] if items else None)


async def get_availability(
    db: AsyncSession, content_id: uuid.UUID, connected: set[str]
) -> tuple[list[SourceResponse], SourceResponse | None, bool]:
    content = (
        await db.execute(
            select(Content).where(Content.id == content_id).options(selectinload(Content.sources))
        )
    ).scalar_one_or_none()
    if content is None:
        return [], None, False
    providers = await _provider_map(db)
    items, best = sources_to_response(list(content.sources), providers, connected)
    return items, best, False
