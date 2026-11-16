"""App base de Celery para workers."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "manga_colorizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.task_default_queue = "default"
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
