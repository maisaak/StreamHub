from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "streamhub", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BROKER_URL
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    beat_schedule={
        "refresh-catalog-6h": {
            "task": "app.worker.tasks.refresh_catalog",
            "schedule": crontab(hour="*/6", minute=0),
        },
        "check-new-releases-daily": {
            "task": "app.worker.tasks.check_new_releases",
            "schedule": crontab(hour=9, minute=0),
        },
        "prune-histories-daily": {
            "task": "app.worker.tasks.prune_histories",
            "schedule": crontab(hour=3, minute=30),
        },
    },
)

# import tasks so worker registers them
from app.worker import tasks  # noqa: E402,F401
