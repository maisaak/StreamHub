"""Shared helpers for mock-backed providers (demo catalog + real-API-ready structure)."""

from __future__ import annotations

from app.providers._catalog import CatalogRow
from app.providers.base import AvailabilityInfo, ProviderItem
from app.services.matcher_service import gated_fuzzy_score
from app.utils.normalizers import normalize_title


def match_catalog(
    catalog: list[CatalogRow], query: str, year: int | None = None, threshold: int = 60
) -> list[CatalogRow]:
    q = normalize_title(query, remove_stopwords=False)
    if not q:
        return []
    scored: list[tuple[int, CatalogRow]] = []
    for row in catalog:
        title = normalize_title(row.get("title", ""), remove_stopwords=False)
        orig = normalize_title(row.get("original_title", ""), remove_stopwords=False)
        substring = (q in title) if title else False
        substring = substring or ((q in orig) if orig else False)
        if substring:
            score = 95.0
        elif len(q) < 4:
            continue  # short queries: substring only, no fuzzy guesswork
        else:
            score = max(
                gated_fuzzy_score(q, title) if title else 0,
                gated_fuzzy_score(q, orig) if orig else 0,
            )
        if year and row.get("year") and abs(int(row["year"]) - year) > 1:
            score -= 25
        if score >= threshold:
            scored.append((int(score), row))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:20]]


def to_item(provider_id: str, base_url: str, row: CatalogRow) -> ProviderItem:
    ext = str(row["external_id"])
    return ProviderItem(
        external_id=ext,
        title=row.get("title", ""),
        original_title=row.get("original_title", ""),
        year=row.get("year"),
        content_type=row.get("content_type", "movie"),
        description=row.get("description", ""),
        poster_url=row.get("poster_url", ""),
        genres=list(row.get("genres", [])),
        rating_kinopoisk=row.get("rating_kinopoisk"),
        rating_imdb=row.get("rating_imdb"),
        tmdb_id=row.get("tmdb_id"),
        price=row.get("price"),
        is_subscription=bool(row.get("is_subscription", False)),
        quality=row.get("quality", "HD"),
        url=row.get("url") or f"{base_url}/watch/{ext}",
    )


def to_availability(
    provider_id: str, base_url: str, scheme: str | None, row: CatalogRow
) -> AvailabilityInfo:
    ext = str(row["external_id"])
    return AvailabilityInfo(
        external_id=ext,
        url=row.get("url") or f"{base_url}/watch/{ext}",
        deep_link=f"{scheme}://open/{ext}" if scheme else None,
        price=row.get("price"),
        is_subscription=bool(row.get("is_subscription", False)),
        quality=row.get("quality", "HD"),
        available=True,
    )
