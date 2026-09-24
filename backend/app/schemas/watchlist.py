from __future__ import annotations

from pydantic import BaseModel

from app.schemas.content import ContentCard


class WatchlistAdd(BaseModel):
    content_id: str
    notify_on_release: bool = False


class WatchlistItem(BaseModel):
    id: int
    added_at: str
    notify_on_release: bool
    content: ContentCard
