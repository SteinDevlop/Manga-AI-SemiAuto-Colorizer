"""Celery worker entrypoint for CPU-bound tasks.

Independent process of the same FastAPI monolith (not a microservice).
Only processes Celery tasks -- no heavy inference inside HTTP endpoints.
Handles hashing, normalization, panels, and auxiliary operations (no GPU).
"""

from __future__ import annotations

import logging
import os

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Queue name(s) consumed by this worker, overridden by environment variable.
WORKER_CPU_QUEUES: str = os.getenv("WORKER_CPU_QUEUES", "WORKER_CPU_QUEUES")

# Concurrency for the CPU worker: defaults to the available CPU count,
# overridable through the WORKER_CPU_CONCURRENCY environment variable.
_cpu_env = os.getenv("WORKER_CPU_CONCURRENCY")
WORKER_CPU_CONCURRENCY: int = int(_cpu_env) if _cpu_env else (os.cpu_count() or 2)


def configure() -> None:
    """Apply worker-specific Celery configuration."""
    celery_app.conf.worker_concurrency = WORKER_CPU_CONCURRENCY
    logger.info(
        "CPU worker configured: queues=%s concurrency=%s",
        WORKER_CPU_QUEUES,
        WORKER_CPU_CONCURRENCY,
    )


def main() -> None:
    """Start the CPU worker process."""
    configure()
    celery_app.worker_main(
        argv=[
            "worker",
            f"--queues={WORKER_CPU_QUEUES}",
            f"--concurrency={WORKER_CPU_CONCURRENCY}",
        ]
    )


if __name__ == "__main__":
    main()
