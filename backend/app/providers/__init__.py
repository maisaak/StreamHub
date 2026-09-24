from __future__ import annotations

from app.providers.base import AvailabilityInfo, BaseProvider, ProviderItem
from app.providers.ivi import IviProvider
from app.providers.kinopoisk import KinopoiskProvider
from app.providers.okko import OkkoProvider
from app.providers.premier import PremierProvider
from app.providers.rutube import RutubeProvider
from app.providers.start import StartProvider
from app.providers.wink import WinkProvider
from app.providers.youtube import YoutubeProvider

_REGISTRY: dict[str, BaseProvider] = {
    p.provider_id: p
    for p in [
        KinopoiskProvider(),
        IviProvider(),
        OkkoProvider(),
        YoutubeProvider(),
        RutubeProvider(),
        WinkProvider(),
        StartProvider(),
        PremierProvider(),
    ]
}


def all_providers() -> list[BaseProvider]:
    return list(_REGISTRY.values())


def get_provider(provider_id: str) -> BaseProvider | None:
    return _REGISTRY.get(provider_id)


__all__ = ["BaseProvider", "ProviderItem", "AvailabilityInfo", "all_providers", "get_provider"]
