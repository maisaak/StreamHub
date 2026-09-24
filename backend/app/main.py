from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import auth, content, history, preferences, providers, search, watchlist
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import get_db

structlog.configure(processors=[structlog.processors.JSONRenderer()])
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    from app.db.seed import seed_all
    from app.db.session import async_session_factory, init_db

    await init_db()
    try:
        async with async_session_factory() as db:
            await seed_all(db)
    except Exception as e:
        log.error("seed_failed", error=str(e))
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="StreamHub API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[*settings.cors_origins, "http://localhost:80", "http://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    for r in (
        auth.router,
        providers.router,
        search.router,
        content.router,
        watchlist.router,
        history.router,
        preferences.router,
    ):
        app.include_router(r, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/s/{slug}")
    async def short_redirect(slug: str, db: AsyncSession = Depends(get_db)):  # type: ignore[no-untyped-def]
        from app.db.models import ShortLink

        link = (
            await db.execute(select(ShortLink).where(ShortLink.slug == slug))
        ).scalar_one_or_none()
        if not link:
            return {"detail": "Ссылка не найдена или устарела."}
        link.clicks += 1
        await db.commit()
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/content/{link.content_id}", status_code=302
        )

    return app


app = create_app()
