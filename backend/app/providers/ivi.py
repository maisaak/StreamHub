from __future__ import annotations

from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

KEYS = {
    "matrix",
    "interstellar",
    "dune",
    "gentlemen",
    "slovo",
    "wednesday",
    "avatar2",
    "barbie",
    "wick4",
    "cheburashka",
    "cyberderevnya",
    "kuhnya",
    "friends",
    "office",
    "potter",
    "squid",
    "prostokvashino",
    "oppenheimer",
    "trigger",
    "smeshariki",
    "vyzov",
    "brat2",
}

CATALOG = [
    {**r, "external_id": f"ivi-{r['key']}", "is_subscription": True, "price": None, "quality": "4K"}
    for r in FULL_CATALOG
    if r["key"] in KEYS
]


class IviProvider(BaseProvider):
    provider_id = "ivi"
    name = "Иви"
    base_url = "https://www.ivi.ru"
    brand_color = "#EB1537"
    deep_scheme = "ivi"
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
