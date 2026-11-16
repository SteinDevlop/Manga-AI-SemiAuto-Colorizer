"""Celery worker entrypoint for GPU-bound tasks.

Independent process of the same FastAPI monolith (not a microservice).
Only processes Celery tasks -- no heavy inference inside HTTP endpoints.
Limits concurrency to 1 (ADR-006) for large resident models and logs VRAM,
duration, resolution, and model per execution with job_id (structured logs).
"""

from __future__ import annotations

import logging
import os
from typing import Final

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Queue name(s) consumed by this worker, overridden by environment variable.
WORKER_GPU_QUEUES: str = os.getenv("WORKER_GPU_QUEUES", "WORKER_GPU_QUEUES")

# GPU concurrency is fixed at 1 for large resident models (ADR-006).
WORKER_GPU_CONCURRENCY: Final[int] = 1

# Name of the simulated resident model loaded at worker startup.
RESIDENT_MODEL: str | None = None


def load_resident_model() -> str:
    """Load the simulated resident model into memory at worker startup.

    This is a simulation: no real ML framework or GPU allocation happens here.
    """
    global RESIDENT_MODEL
    model_name = os.getenv("GPU_RESIDENT_MODEL", "manga-colorizer-v1")
    logger.info("Loading resident GPU model: %s", model_name)
    RESIDENT_MODEL = model_name
    return model_name


def log_job_execution(
    job_id: str,
    duration_ms: float,
    resolution: str,
    vram_mb: float,
    model: str | None = None,
) -> None:
    """Emit a structured log entry for a single GPU job execution.

    Fields: job_id, duration_ms, resolution, model, vram_mb.
    """
    logger.info(
        "job_execution job_id=%s duration_ms=%.2f resolution=%s model=%s vram_mb=%.2f",
        job_id,
        duration_ms,
        resolution,
        model if model is not None else RESIDENT_MODEL,
        vram_mb,
    )


def configure() -> None:
    """Apply worker-specific Celery configuration."""
    celery_app.conf.worker_concurrency = WORKER_GPU_CONCURRENCY
    logger.info(
        "GPU worker configured: queues=%s concurrency=%s resident_model=%s",
        WORKER_GPU_QUEUES,
        WORKER_GPU_CONCURRENCY,
        RESIDENT_MODEL,
    )


def main() -> None:
    """Start the GPU worker process."""
    load_resident_model()
    configure()
    celery_app.worker_main(
        argv=[
            "worker",
            f"--queues={WORKER_GPU_QUEUES}",
            f"--concurrency={WORKER_GPU_CONCURRENCY}",
        ]
    )


if __name__ == "__main__":
    main()
