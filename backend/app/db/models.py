from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, new_uuid


class Theme(str, enum.Enum):
    auto = "auto"
    light = "light"
    dark = "dark"


class Lang(str, enum.Enum):
    ru = "ru"
    en = "en"


class ContentType(str, enum.Enum):
    movie = "movie"
    series = "series"
    video = "video"


class Quality(str, enum.Enum):
    any = "any"
    SD = "SD"
    HD = "HD"
    UHD_4K = "4K"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_theme: Mapped[Theme] = mapped_column(SAEnum(Theme), default=Theme.auto)
    preferred_language: Mapped[Lang] = mapped_column(SAEnum(Lang), default=Lang.ru)

    providers: Mapped[list[UserProvider]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[UserPreferences | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # slug
    name: Mapped[str] = mapped_column(String(120))
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    base_url: Mapped[str] = mapped_column(String(500), default="")
    brand_color: Mapped[str] = mapped_column(String(16), default="#000000")
    requires_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)


class UserProvider(Base):
    __tablename__ = "user_providers"
    __table_args__ = (UniqueConstraint("user_id", "provider_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider_id: Mapped[str] = mapped_column(String(32), ForeignKey("providers.id"), index=True)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="providers")
    provider: Mapped[Provider] = relationship()


class Content(Base):
    __tablename__ = "content"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=new_uuid)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType), default=ContentType.movie
    )
    title: Mapped[str] = mapped_column(String(500), index=True)
    original_title: Mapped[str] = mapped_column(String(500), default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    poster_url: Mapped[str] = mapped_column(String(1000), default="")
    backdrop_url: Mapped[str] = mapped_column(String(1000), default="")
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_kinopoisk: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_imdb: Mapped[float | None] = mapped_column(Float, nullable=True)
    popularity: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sources: Mapped[list[ContentSource]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_content_title_year", "title", "year"),)


class ContentSource(Base):
    __tablename__ = "content_sources"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_id"),
        Index("ix_sources_content_provider", "content_id", "provider_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("content.id", ondelete="CASCADE")
    )
    provider_id: Mapped[str] = mapped_column(String(32), ForeignKey("providers.id"))
    external_id: Mapped[str] = mapped_column(String(255), default="")
    external_url: Mapped[str] = mapped_column(String(1000), default="")
    deep_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    quality: Mapped[str] = mapped_column(String(16), default="HD")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    content: Mapped[Content] = relationship(back_populates="sources")
    provider: Mapped[Provider] = relationship()


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id"),
        Index("ix_watchlist_user_added", "user_id", "added_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"))
    content_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("content.id", ondelete="CASCADE")
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notify_on_release: Mapped[bool] = mapped_column(Boolean, default=False)

    content: Mapped[Content] = relationship()


class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = (Index("ix_search_history_user_time", "user_id", "searched_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    query: Mapped[str] = mapped_column(String(500))
    searched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ViewHistory(Base):
    __tablename__ = "view_history"
    __table_args__ = (Index("ix_view_history_user_time", "user_id", "viewed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("content.id", ondelete="CASCADE")
    )
    provider_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("providers.id"), nullable=True
    )
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    watched: Mapped[bool] = mapped_column(Boolean, default=False)  # "Уже смотрел"

    content: Mapped[Content] = relationship()


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    only_my_subscriptions: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_quality: Mapped[str] = mapped_column(String(8), default="any")
    hide_watched: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_play_next: Mapped[bool] = mapped_column(Boolean, default=True)
    favorite_genres: Mapped[list[str]] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="preferences")


class ShortLink(Base):
    __tablename__ = "short_links"

    slug: Mapped[str] = mapped_column(String(32), primary_key=True)
    content_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("content.id", ondelete="CASCADE")
    )
    provider_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    clicks: Mapped[int] = mapped_column(Integer, default=0)
