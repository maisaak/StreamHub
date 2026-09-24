from __future__ import annotations

import httpx

from app.config import settings
from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

KEYS = {
    "matrix",
    "interstellar",
    "dune",
    "oppenheimer",
    "brat2",
    "gentlemen",
    "slovo",
    "wednesday",
    "avatar2",
    "barbie",
    "wick4",
    "cheburashka",
    "vyzov",
    "cyberderevnya",
    "trigger",
    "kuhnya",
    "friends",
    "breaking",
    "office",
    "aot",
    "potter",
    "prostokvashino",
    "squid",
    "smeshariki",
}

CATALOG = [
    {**r, "external_id": f"kp-{r['key']}", "is_subscription": True, "price": None, "quality": "4K"}
    for r in FULL_CATALOG
    if r["key"] in KEYS
]


class KinopoiskProvider(BaseProvider):
    provider_id = "kinopoisk"
    name = "Кинопоиск"
    base_url = "https://hd.kinopoisk.ru"
    brand_color = "#FF6A00"
    deep_scheme = "kinopoisk"
    requires_subscription = True

    async def search(self, query: str, year: int | None = None) -> list[ProviderItem]:
        if settings.KINOPOISK_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=5) as c:
                    resp = await c.get(
                        "https://api.kinopoisk.dev/v1.4/movie/search",
                        params={"query": query},
                        headers={"X-API-KEY": settings.KINOPOISK_API_KEY},
                    )
                    if resp.status_code == 200:
                        return [
                            to_item(
                                self.provider_id,
                                self.base_url,
                                {
                                    **r,
                                    "external_id": f"kp-{r['key']}",
                                    "is_subscription": True,
                                    "quality": "4K",
                                },
                            )
                            for r in match_catalog(CATALOG, query, year)
                        ]
            except Exception:
                pass
        return [
            to_item(self.provider_id, self.base_url, r) for r in match_catalog(CATALOG, query, year)
        ]

    async def get_details(self, external_id: str) -> ProviderItem | None:
        for r in CATALOG:
            if r["external_id"] == external_id:
                return to_item(self.provider_id, self.base_url, r)
        return None

    async def get_availability(self, external_id: str) -> AvailabilityInfo | None:
        for r in CATALOG:
            if r["external_id"] == external_id:
                return to_availability(self.provider_id, self.base_url, self.deep_scheme, r)
        return None
