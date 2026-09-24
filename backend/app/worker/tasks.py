from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from datetime import UTC
from typing import Any, TypeVar

import structlog

from app.worker.celery_app import celery_app

log = structlog.get_logger()


T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


@celery_app.task(name="app.worker.tasks.refresh_catalog")  # type: ignore[untyped-decorator]
def refresh_catalog() -> dict[str, object]:
    """Re-check availability timestamps (mock: touch last_checked_at)."""

    async def _inner() -> int:
        from datetime import datetime

        from sqlalchemy import select

        from app.db.models import ContentSource
        from app.db.session import async_session_factory

        async with async_session_factory() as db:
            rows = (await db.execute(select(ContentSource).limit(2000))).scalars().all()
            for r in rows:
                r.last_checked_at = datetime.now(UTC)
            await db.commit()
            return len(rows)

    try:
        n = _run(_inner())
        log.info("refresh_catalog_done", sources=n)
        return {"refreshed": n}
    except Exception as e:
        log.error("refresh_catalog_failed", error=str(e))
        return {"refreshed": 0, "error": str(e)}


@celery_app.task(name="app.worker.tasks.check_new_releases")  # type: ignore[untyped-decorator]
def check_new_releases() -> dict[str, object]:
    log.info("check_new_releases_done")
    return {"checked": True}


@celery_app.task(name="app.worker.tasks.prune_histories")  # type: ignore[untyped-decorator]
def prune_histories() -> dict[str, object]:
    async def _inner() -> int:
        from sqlalchemy import delete, desc, select

        from app.db.models import SearchHistory
        from app.db.session import async_session_factory

        total = 0
        async with async_session_factory() as db:
            user_ids = (await db.execute(select(SearchHistory.user_id).distinct())).scalars().all()
            for uid in user_ids:
                ids = (
                    (
                        await db.execute(
                            select(SearchHistory.id)
                            .where(SearchHistory.user_id == uid)
                            .order_by(desc(SearchHistory.searched_at), desc(SearchHistory.id))
                            .offset(100)
                        )
                    )
                    .scalars()
                    .all()
                )
                if ids:
                    await db.execute(delete(SearchHistory).where(SearchHistory.id.in_(ids)))
                    total += len(ids)
            await db.commit()
        return total

    try:
        n = _run(_inner())
        return {"pruned": n}
    except Exception as e:
        return {"pruned": 0, "error": str(e)}
