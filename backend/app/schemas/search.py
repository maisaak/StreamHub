from __future__ import annotations

from pydantic import BaseModel

from app.schemas.content import ContentCard


class SearchResponse(BaseModel):
    items: list[ContentCard]
    total: int
    partial: bool = False
    failed_providers: list[str] = []
    suggestions: list[str] = []
    took_ms: int = 0


class SuggestItem(BaseModel):
    kind: str  # "history" | "content"
    text: str
    content_id: str | None = None
    poster_url: str = ""
    year: int | None = None


class SuggestResponse(BaseModel):
    items: list[SuggestItem]


class HistoryItem(BaseModel):
    id: int
    query: str
    searched_at: str
