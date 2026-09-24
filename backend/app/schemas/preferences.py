from __future__ import annotations

from pydantic import BaseModel


class PreferencesResponse(BaseModel):
    only_my_subscriptions: bool = False
    preferred_quality: str = "any"
    hide_watched: bool = False
    auto_play_next: bool = True
    favorite_genres: list[str] = []

    model_config = {"from_attributes": True}


class PreferencesPatch(BaseModel):
    only_my_subscriptions: bool | None = None
    preferred_quality: str | None = None
    hide_watched: bool | None = None
    auto_play_next: bool | None = None
    favorite_genres: list[str] | None = None
