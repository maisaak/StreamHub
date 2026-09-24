from __future__ import annotations

from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

KEYS = {
    "slovo",
    "cyberderevnya",
    "trigger",
    "kuhnya",
    "smeshariki",
    "vyzov",
    "cheburashka",
    "wednesday",
    "squid",
    "breaking",
    "office",
    "aot",
    "friends",
    "gentlemen",
    "brat2",
    "potter",
}

CATALOG = [
    {
        **r,
        "external_id": f"start-{r['key']}",
        "is_subscription": True,
        "price": None,
        "quality": "HD",
    }
    for r in FULL_CATALOG
    if r["key"] in KEYS
]


class StartProvider(BaseProvider):
    provider_id = "start"
    name = "START"
    base_url = "https://start.ru"
    brand_color = "#00D1FF"
    deep_scheme = "start"
    requires_subscription = True

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
