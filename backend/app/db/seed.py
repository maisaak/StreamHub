"""Seed providers + demo catalog + sources (mirrors provider mock availability)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Content, ContentSource, ContentType, Provider
from app.providers import all_providers
from app.providers._catalog import FULL_CATALOG

# provider_id -> {key: (is_subscription, price, quality, external_id)}
AVAILABILITY: dict[str, dict[str, tuple[bool, float | None, str, str]]] = {}


def _build() -> None:
    from app.providers import ivi, kinopoisk, okko, premier, rutube, start, wink, youtube

    for mod, pid in [
        (kinopoisk, "kinopoisk"),
        (ivi, "ivi"),
        (okko, "okko"),
        (youtube, "youtube"),
        (rutube, "rutube"),
        (wink, "wink"),
        (start, "start"),
        (premier, "premier"),
    ]:
        AVAILABILITY[pid] = {}
        for row in mod.CATALOG:
            ext = str(row["external_id"])
            price = row.get("price")
            AVAILABILITY[pid][str(row["key"])] = (
                bool(row["is_subscription"]),
                float(price) if price is not None else None,
                str(row.get("quality", "HD")),
                ext,
            )


_build()

PRIORITY = {
    "kinopoisk": 10,
    "ivi": 20,
    "okko": 30,
    "wink": 40,
    "start": 50,
    "premier": 60,
    "youtube": 70,
    "rutube": 80,
}


async def seed_all(db: AsyncSession) -> None:
    # providers
    for p in all_providers():
        exists = (
            await db.execute(select(Provider).where(Provider.id == p.provider_id))
        ).scalar_one_or_none()
        if not exists:
            db.add(
                Provider(
                    id=p.provider_id,
                    name=p.name,
                    logo_url=f"/logos/{p.provider_id}.svg",
                    base_url=p.base_url,
                    brand_color=p.brand_color,
                    requires_subscription=p.requires_subscription,
                    is_active=True,
                    priority=PRIORITY.get(p.provider_id, 100),
                )
            )
    await db.commit()

    count = (await db.execute(select(func.count()).select_from(Content))).scalar() or 0
    if count > 0:
        return

    prov_map = {p.provider_id: p for p in all_providers()}
    for row in FULL_CATALOG:
        c = Content(
            tmdb_id=row.get("tmdb_id"),
            content_type=ContentType(row.get("content_type", "movie")),
            title=row["title"],
            original_title=row.get("original_title", "") or "",
            year=row.get("year"),
            description=row.get("description", ""),
            poster_url=row.get("poster_url", ""),
            backdrop_url=row.get("backdrop_url", ""),
            genres=list(row.get("genres", [])),
            runtime_minutes=row.get("runtime_minutes"),
            rating_kinopoisk=row.get("rating_kinopoisk"),
            rating_imdb=row.get("rating_imdb"),
            popularity=float(row.get("popularity", 50)),
        )
        db.add(c)
        await db.flush()
        for pid, keys in AVAILABILITY.items():
            if row["key"] not in keys:
                continue
            is_sub, price, quality, ext = keys[row["key"]]
            p = prov_map[pid]
            db.add(
                ContentSource(
                    content_id=c.id,
                    provider_id=pid,
                    external_id=ext,
                    external_url=f"{p.base_url}/watch/{ext}",
                    deep_link=f"{p.deep_scheme}://open/{ext}" if p.deep_scheme else None,
                    price=price,
                    is_subscription=is_sub,
                    quality=quality,
                )
            )
    await db.commit()
