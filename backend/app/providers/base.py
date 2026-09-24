from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderItem:
    external_id: str
    title: str
    original_title: str = ""
    year: int | None = None
    content_type: str = "movie"
    description: str = ""
    poster_url: str = ""
    genres: list[str] = field(default_factory=list)
    rating_kinopoisk: float | None = None
    rating_imdb: float | None = None
    tmdb_id: int | None = None
    price: float | None = None
    is_subscription: bool = False
    quality: str = "HD"
    url: str = ""


@dataclass
class AvailabilityInfo:
    external_id: str
    url: str
    deep_link: str | None = None
    price: float | None = None
    is_subscription: bool = False
    quality: str = "HD"
    available: bool = True


class BaseProvider(ABC):
    provider_id: str = ""
    name: str = ""
    base_url: str = ""
    brand_color: str = "#000000"
    deep_scheme: str | None = None
    requires_subscription: bool = False

    @abstractmethod
    async def search(self, query: str, year: int | None = None) -> list[ProviderItem]: ...

    @abstractmethod
    async def get_details(self, external_id: str) -> ProviderItem | None: ...

    @abstractmethod
    async def get_availability(self, external_id: str) -> AvailabilityInfo | None: ...

    def build_deep_link(self, external_id: str) -> str | None:
        if self.deep_scheme:
            return f"{self.deep_scheme}://open/{external_id}"
        return None

    def build_url(self, external_id: str) -> str:
        return f"{self.base_url}/watch/{external_id}"
