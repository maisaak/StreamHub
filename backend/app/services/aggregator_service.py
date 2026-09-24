"""Unified search pipeline: parallel providers → normalize → match → dedup → rank → cache."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid

import structlog
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.redis import get_redis
from app.db.models import Content, Provider
from app.providers import all_providers
from app.providers.base import ProviderItem
from app.schemas.content import ContentCard, SourceResponse
from app.services import matcher_service
from app.services.availability_service import sources_to_response

log = structlog.get_logger()


async def _search_provider(
    pid: str, query: str, year: int | None
) -> tuple[str, list[ProviderItem] | Exception]:
    from app.providers import get_provider

    prov = get_provider(pid)
    assert prov is not None
    try:
        items = await asyncio.wait_for(prov.search(query, year), timeout=settings.PROVIDER_TIMEOUT)
        return pid, items
    except Exception as e:  # noqa: BLE001 - partial results must not break search
        log.warning("provider_search_failed", provider=pid, error=str(e))
        return pid, e


def _cache_key(query: str, year: int | None, ctype: str | None, connected: set[str]) -> str:
    raw = f"{query}|{year}|{ctype}|{sorted(connected)}"
    return "search:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _db_candidates(
    db: AsyncSession, query: str, ctype: str | None, year: int | None, limit: int = 60
) -> list[Content]:
    from app.utils.normalizers import normalize_title

    q = query.strip()
    stmt = select(Content).options(selectinload(Content.sources))
    if ctype:
        stmt = stmt.where(Content.content_type == ctype)
    if year:
        stmt = stmt.where(Content.year == year)
    rows = (await db.execute(stmt.limit(400))).scalars().all()
    if not q:
        return sorted(rows, key=lambda c: -(c.popularity or 0))[:limit]
    nq = normalize_title(q, remove_stopwords=False)
    scored: list[tuple[float, Content]] = []
    for c in rows:
        titles = [c.title or "", c.original_title or ""]
        best = 0
        for t in titles:
            nt = normalize_title(t, remove_stopwords=False)
            if not nt:
                continue
            if nq == nt:
                best = max(best, 100)
            elif nq in nt or nt in nq:
                best = max(best, 90)
            elif len(nq) >= 4:
                best = max(best, matcher_service.gated_fuzzy_score(q, t))
        # trigram-ish fallback: token overlap (only for multi-char queries)
        if best < 60 and len(nq) >= 4:
            qtokens = {w for w in nq.split() if len(w) >= 4}
            for t in titles:
                toks = set(normalize_title(t, remove_stopwords=False).split())
                if qtokens & toks:
                    best = max(best, 62)
        # pg_trgm emulation: strict bar so typos match but junk doesn't
        if best >= 60:
            boost = (c.popularity or 0) / 100
            scored.append((best + boost, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:limit]]


def _merge_provider_items(
    db_contents: list[Content], provider_results: dict[str, list[ProviderItem]]
) -> tuple[list[Content], list[ProviderItem]]:
    """Match provider items onto DB contents; return (matched_contents, unmatched_items)."""
    matched_ids: dict[str, Content] = {}
    unmatched: list[ProviderItem] = []
    for _pid, items in provider_results.items():
        for it in items:
            m = matcher_service.match_item(it, db_contents)
            if m is None:
                unmatched.append(it)
            else:
                matched_ids[str(m.id)] = m
    # keep db order first
    matched = [c for c in db_contents if str(c.id) in matched_ids]
    return matched, unmatched


async def _provider_map(db: AsyncSession) -> dict[str, Provider]:
    rows = (await db.execute(select(Provider))).scalars().all()
    return {p.id: p for p in rows}


def content_to_card(c: Content, providers: dict[str, Provider], connected: set[str]) -> ContentCard:
    items, best = sources_to_response(list(c.sources or []), providers, connected)
    pids = sorted({s.provider_id for s in (c.sources or [])})
    free = any((not s.is_subscription and s.price is None) for s in (c.sources or []))
    return ContentCard(
        id=c.id,
        content_type=c.content_type.value
        if hasattr(c.content_type, "value")
        else str(c.content_type),
        title=c.title,
        original_title=c.original_title or "",
        year=c.year,
        poster_url=c.poster_url or "",
        backdrop_url=c.backdrop_url or "",
        genres=list(c.genres or []),
        rating_kinopoisk=c.rating_kinopoisk,
        rating_imdb=c.rating_imdb,
        runtime_minutes=c.runtime_minutes,
        providers=pids,
        best_source=best,
        free=free,
    )


def provider_item_to_card(
    pid: str, it: ProviderItem, providers: dict[str, Provider], connected: set[str]
) -> ContentCard:
    p = providers.get(pid)
    src = SourceResponse(
        provider_id=pid,
        provider_name=p.name if p else pid,
        brand_color=p.brand_color if p else "#000000",
        logo_url=p.logo_url if p else "",
        external_url=it.url,
        deep_link=None,
        price=it.price,
        is_subscription=it.is_subscription,
        quality=it.quality,
        connected=pid in connected,
        rank=0,
    )
    # deterministic pseudo-id for provider-only items
    pseudo = uuid.uuid5(uuid.NAMESPACE_URL, f"{pid}:{it.external_id}")
    return ContentCard(
        id=pseudo,
        content_type=it.content_type,
        title=it.title,
        original_title=it.original_title,
        year=it.year,
        poster_url=it.poster_url,
        backdrop_url="",
        genres=list(it.genres),
        rating_kinopoisk=it.rating_kinopoisk,
        rating_imdb=it.rating_imdb,
        runtime_minutes=None,
        providers=[pid],
        best_source=src,
        free=(it.price is None and not it.is_subscription),
    )


async def unified_search(
    db: AsyncSession,
    query: str,
    ctype: str | None = None,
    year: int | None = None,
    connected: set[str] | None = None,
    only_my: bool = False,
    free_only: bool = False,
    quality: str | None = None,
    genres: list[str] | None = None,
    min_rating: float | None = None,
    max_duration: int | None = None,
    min_duration: int | None = None,
) -> tuple[list[ContentCard], bool, list[str], int]:
    started = time.monotonic()
    connected = connected or set()
    redis = await get_redis()
    ckey = _cache_key(query, year, ctype, connected)
    if not any([only_my, free_only, quality, genres, min_rating, max_duration, min_duration]):
        try:  # noqa: SIM105
            cached = await redis.get(ckey)
            if cached:
                data = json.loads(cached)
                cached_items = [ContentCard(**x) for x in data["items"]]
                return (
                    cached_items,
                    data.get("partial", False),
                    data.get("failed", []),
                    int((time.monotonic() - started) * 1000),
                )
        except Exception:
            pass

    # 1. parallel providers
    provs = [p for p in all_providers()]
    results = await asyncio.gather(*[_search_provider(p.provider_id, query, year) for p in provs])
    provider_results: dict[str, list[ProviderItem]] = {}
    failed: list[str] = []
    for pid, res in results:
        if isinstance(res, Exception):
            failed.append(pid)
        else:
            provider_results[pid] = res

    # 2. db candidates
    db_contents = await _db_candidates(db, query, ctype, year)
    providers = await _provider_map(db)

    # 3-4. match + dedup
    matched, unmatched = _merge_provider_items(db_contents, provider_results)
    # db items that fuzzy-matched query but had no provider hit still count (catalog search)
    ordered: list[Content] = []
    seen: set[str] = set()
    for c in db_contents:
        if str(c.id) not in seen:
            seen.add(str(c.id))
            ordered.append(c)

    cards: list[ContentCard] = [content_to_card(c, providers, connected) for c in ordered]
    # provider-only items appended (not in catalog)
    dedup_titles = {(c.title.lower(), c.year) for c in ordered}
    for pid, prov_items in provider_results.items():
        for it in prov_items:
            key = (it.title.lower(), it.year)
            if key in dedup_titles:
                continue
            dedup_titles.add(key)
            cards.append(provider_item_to_card(pid, it, providers, connected))

    # filters
    if genres:
        gl = {g.lower() for g in genres}
        cards = [c for c in cards if gl & {g.lower() for g in c.genres}]
    if min_rating is not None:
        cards = [c for c in cards if (c.rating_kinopoisk or c.rating_imdb or 0) >= min_rating]
    if only_my and connected:
        cards = [c for c in cards if set(c.providers) & connected]
    if free_only:
        cards = [c for c in cards if c.free]
    if quality and quality != "any":
        order = {"SD": 0, "HD": 1, "4K": 2}
        want = order.get(quality, 1)
        cards = [c for c in cards if c.best_source and order.get(c.best_source.quality, 1) >= want]

    partial = len(failed) > 0
    took_ms = int((time.monotonic() - started) * 1000)

    if not any([only_my, free_only, quality, genres, min_rating, max_duration, min_duration]):
        try:  # noqa: SIM105
            await redis.set(
                ckey,
                json.dumps(
                    {
                        "items": [c.model_dump(mode="json") for c in cards[:50]],
                        "partial": partial,
                        "failed": failed,
                    }
                ),
                ex=settings.SEARCH_CACHE_TTL,
            )
        except Exception:
            pass
    return cards[:50], partial, failed, took_ms


async def similar_content(
    db: AsyncSession, content_id: uuid.UUID, connected: set[str], limit: int = 12
) -> list[ContentCard]:
    base = (await db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
    if base is None:
        return []
    rows = (
        (
            await db.execute(
                select(Content)
                .options(selectinload(Content.sources))
                .where(Content.id != content_id)
                .limit(200)
            )
        )
        .scalars()
        .all()
    )
    providers = await _provider_map(db)
    bgenres = set(base.genres or [])

    def score(c: Content) -> float:
        s = float(len(bgenres & set(c.genres or [])) * 10)
        if c.content_type == base.content_type:
            s += 5
        s += float(c.popularity or 0) / 20
        return s

    ranked = sorted(rows, key=score, reverse=True)[:limit]
    return [content_to_card(c, providers, connected) for c in ranked]


async def catalog_suggestions(db: AsyncSession, query: str, limit: int = 5) -> list[str]:
    """Similar titles for 'nothing found' block (trigram-like)."""
    rows = (await db.execute(select(Content.title).limit(400))).scalars().all()
    scored = sorted(
        ((matcher_service.gated_fuzzy_score(query, t), t) for t in rows if t),
        key=lambda x: -x[0],
    )
    close = [t for s, t in scored if s >= 55][:limit]
    if close:
        return close
    popular_rows = (
        (await db.execute(select(Content.title).order_by(desc(Content.popularity)).limit(limit)))
        .scalars()
        .all()
    )
    return [t for t in popular_rows if t]
