from __future__ import annotations

from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

KEYS = {
    "cosmos",
    "standup",
    "slovo",
    "cyberderevnya",
    "smeshariki",
    "prostokvashino",
    "kuhnya",
    "trigger",
    "brat2",
    "cheburashka",
    "vyzov",
    "potter",
    "friends",
    "office",
    "breaking",
}

CATALOG = [
    {**r, "external_id": f"rt-{r['key']}", "is_subscription": False, "price": None, "quality": "HD"}
    for r in FULL_CATALOG
    if r["key"] in KEYS
]


class RutubeProvider(BaseProvider):
    provider_id = "rutube"
    name = "Rutube"
    base_url = "https://rutube.ru"
    brand_color = "#00A6E0"
    deep_scheme = "rutube"
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
