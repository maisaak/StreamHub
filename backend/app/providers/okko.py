from __future__ import annotations

from app.providers._catalog import FULL_CATALOG
from app.providers._mock import match_catalog, to_availability, to_item
from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem

RENT = {
    "matrix": 299,
    "interstellar": 399,
    "dune": 349,
    "oppenheimer": 399,
    "avatar2": 349,
    "wick4": 349,
    "barbie": 299,
    "gentlemen": 299,
    "potter": 299,
    "vyzov": 299,
    "cheburashka": 299,
}
KEYS = set(RENT) | {
    "slovo",
    "wednesday",
    "squid",
    "breaking",
    "friends",
    "office",
    "trigger",
    "kuhnya",
    "aot",
    "cyberderevnya",
}

CATALOG = []
for r in FULL_CATALOG:
    if r["key"] not in KEYS:
        continue
    if r["key"] in RENT:
        CATALOG.append(
            {
                **r,
                "external_id": f"okko-{r['key']}",
                "is_subscription": False,
                "price": RENT[r["key"]],
                "quality": "4K",
            }
        )
    else:
        CATALOG.append(
            {
                **r,
                "external_id": f"okko-{r['key']}",
                "is_subscription": True,
                "price": None,
                "quality": "HD",
            }
        )


class OkkoProvider(BaseProvider):
    provider_id = "okko"
    name = "Okko"
    base_url = "https://okko.tv"
    brand_color = "#3B1D5E"
    deep_scheme = "okko"
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
