from __future__ import annotations

import uuid

from pydantic import BaseModel


class SourceResponse(BaseModel):
    provider_id: str
    provider_name: str = ""
    brand_color: str = "#000000"
    logo_url: str = ""
    external_url: str = ""
    deep_link: str | None = None
    price: float | None = None
    is_subscription: bool = False
    quality: str = "HD"
    connected: bool = False
    rank: int = 99


class ContentCard(BaseModel):
    id: uuid.UUID
    content_type: str
    title: str
    original_title: str = ""
    year: int | None = None
    poster_url: str = ""
    backdrop_url: str = ""
    genres: list[str] = []
    rating_kinopoisk: float | None = None
    rating_imdb: float | None = None
    runtime_minutes: int | None = None
    providers: list[str] = []
    best_source: SourceResponse | None = None
    free: bool = False

    model_config = {"from_attributes": True}


class ContentDetail(ContentCard):
    description: str = ""
    sources: list[SourceResponse] = []
    short_link: str = ""


class SimilarResponse(BaseModel):
    items: list[ContentCard]


class AvailabilityResponse(BaseModel):
    content_id: uuid.UUID
    sources: list[SourceResponse]
    best_source: SourceResponse | None = None
    partial: bool = False


class FeedSection(BaseModel):
    key: str
    title: str
    items: list[ContentCard]


class HomeFeed(BaseModel):
    sections: list[FeedSection]


class ShortLinkResponse(BaseModel):
    short_link: str
    slug: str
