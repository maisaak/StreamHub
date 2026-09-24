from __future__ import annotations

from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

KEYS = {
    "slovo",
    "trigger",
    "kuhnya",
    "cyberderevnya",
    "smeshariki",
    "prostokvashino",
    "standup",
    "cosmos",
    "brat2",
    "vyzov",
    "cheburashka",
    "friends",
    "office",
    "breaking",
    "potter",
    "wednesday",
}

CATALOG = [
    {
        **r,
        "external_id": f"prem-{r['key']}",
        "is_subscription": True,
        "price": None,
        "quality": "HD",
    }
    for r in FULL_CATALOG
    if r["key"] in KEYS
]


class PremierProvider(BaseProvider):
    provider_id = "premier"
    name = "Premier"
    base_url = "https://premier.one"
    brand_color = "#7B2FF7"
    deep_scheme = "premier"
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
