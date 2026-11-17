"""App base de Celery para workers."""

from app.core.config import get_settings
from celery import Celery

settings = get_settings()

celery_app = Celery(
    "manga_colorizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.task_default_queue = "default"
# En Windows el pool 'prefork' falla con PermissionError (billiard shared memory).
# Usar 'solo' en desarrollo local; en Docker Linux se puede volver a 'prefork'.
celery_app.conf.worker_pool = "solo"
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

# Fiabilidad y idempotencia de tareas (ADR-002).
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_default_retry_delay = 30
celery_app.conf.task_max_retries = 3
celery_app.conf.result_expires = 86400  # 24 h

# Rutas de tareas a colas dedicadas (CPU vs GPU).
# colorize_page corre en CPU (no hay GPU en este entorno).
celery_app.conf.task_routes = {
    "app.workers.tasks.analyze_page": {"queue": "WORKER_CPU_QUEUES"},
    "app.workers.tasks.colorize_page": {"queue": "WORKER_CPU_QUEUES"},
}

# Colas por defecto de workers (sobrescritas por variables de entorno).
celery_app.conf.worker_cpu_queues = "WORKER_CPU_QUEUES"
celery_app.conf.worker_gpu_queues = "WORKER_GPU_QUEUES"
