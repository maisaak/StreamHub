from __future__ import annotations

from pydantic import BaseModel

from app.schemas.content import ContentCard


class ViewHistoryItem(BaseModel):
    id: int
    viewed_at: str
    provider_id: str | None = None
    watched: bool = False
    content: ContentCard


class MarkWatchedRequest(BaseModel):
    provider_id: str | None = None
    watched: bool = True
