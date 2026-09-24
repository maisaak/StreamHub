from __future__ import annotations

from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

KEYS = {
    "cosmos",
    "standup",
    "cyberderevnya",
    "smeshariki",
    "prostokvashino",
    "kuhnya",
    "cheburashka",
    "matrix",
    "interstellar",
    "dune",
    "potter",
    "breaking",
    "office",
    "friends",
    "aot",
}

CATALOG = [
    {**r, "external_id": f"yt-{r['key']}", "is_subscription": False, "price": None, "quality": "HD"}
    for r in FULL_CATALOG
    if r["key"] in KEYS
]


class YoutubeProvider(BaseProvider):
    provider_id = "youtube"
    name = "YouTube"
    base_url = "https://www.youtube.com"
    brand_color = "#FF0000"
    deep_scheme = "youtube"
    requires_subscription = False

    async def search(self, query: str, year: int | None = None) -> list[ProviderItem]:
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
