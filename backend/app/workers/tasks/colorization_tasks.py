"""Celery tasks for the colorization pipeline.

Two orchestration tasks are defined:

* :func:`analyze_page` — CPU-bound stage analysis. Simulates page analysis
  progressing 0 to 100 in stages, recording stage/message/timestamp via
  Celery ``update_state`` events.
* :func:`colorize_page` — GPU-bound colorization conditioned on an analysis.
  Simulates staged colorization, records simulated VRAM/duration, and
  returns result path and model version.

Both tasks accept only serializable identifiers (strings) and optional
parameter dicts — never ORM objects or binary payloads. They are idempotent:
when a job is already in a terminal state the task returns without
regenerating artifacts. Heavy inference is intentionally not executed here
(a real GPU adapter is pending for P8).
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from celery import Task

from app.core.exceptions import AppError, ConflictError, InternalError, NotFoundError
from app.infrastructure.database.session import async_session_factory as async_session
from app.modules.colorization.repositories import ColorizationJobRepository
from app.modules.colorization.states import is_terminal, is_valid_transition
from app.workers.celery_app import celery_app

#: Simulated per-stage durations (seconds) for analyze_page.
ANALYZE_STAGES: list[tuple[str, int, str]] = [
    ("loading", 5, "Loading page metadata"),
    ("hashing", 10, "Computing page hash"),
    ("normalizing", 15, "Normalizing page image"),
    ("panels", 20, "Detecting panels"),
    ("finalizing", 10, "Finalizing analysis"),
]

#: Simulated per-stage durations (seconds) for colorize_page.
COLORIZE_STAGES: list[tuple[str, int, str]] = [
    ("segmentation", 15, "Running segmentation"),
    ("coloring", 30, "Applying model colorization"),
    ("refining", 20, "Refining color output"),
    ("finalizing", 10, "Finalizing result"),
]


def _now_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _progress_event(
    *,
    job_id: str,
    stage: str,
    progress: int,
    message: str,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable progress event payload."""
    event: dict[str, Any] = {
        "job_id": job_id,
        "stage": stage,
        "progress": progress,
        "message": message,
        "timestamp": _now_iso(),
    }
    if task_id is not None:
        event["task_id"] = task_id
    return event


async def _fetch_job(job_id: str) -> Any:
    """Fetch the :class:`ColorizationJob` for ``job_id``.

    Returns ``None`` when the job does not exist. Uses a short-lived async
    session so the task does not hold a DB connection across sleeps.
    """
    async with async_session() as session:
        repo = ColorizationJobRepository(session)
        return await repo.get(job_id)


async def _update_job(
    job_id: str,
    *,
    estado: str | None = None,
    progreso: int | None = None,
    mensaje: str | None = None,
    ruta_resultado: str | None = None,
    version_modelo: str | None = None,
    parametros: dict[str, Any] | None = None,
) -> Any:
    """Persist progress/state to the job row and return the updated job."""
    async with async_session() as session:
        repo = ColorizationJobRepository(session)
        kwargs: dict[str, Any] = {}
        if estado is not None:
            kwargs["estado"] = estado
        if progreso is not None:
            kwargs["progreso"] = progreso
        if mensaje is not None:
            kwargs["mensaje"] = mensaje
        if ruta_resultado is not None:
            kwargs["ruta_resultado"] = ruta_resultado
        if version_modelo is not None:
            kwargs["version_modelo"] = version_modelo
        if parametros is not None:
            kwargs["parametros"] = parametros
        return await repo.update(job_id, **kwargs)


def _record_progress(
    self: Task,
    *,
    job_id: str,
    stage: str,
    progress: int,
    message: str,
) -> None:
    """Emit a Celery PROGRESS event with job_id, stage, progress, message."""
    self.update_state(
        state="PROGRESS",
        meta=_progress_event(
            job_id=job_id,
            stage=stage,
            progress=progress,
            message=message,
            task_id=self.request.id,
        ),
    )


def _simulate_stage(duration_seconds: int) -> None:
    """Sleep for a simulated stage duration without blocking the event loop."""
    time.sleep(duration_seconds)


class ColorizationTask(Task):
    """Base task class with idempotency guards shared by analyze/colorize."""

    abstract = True

    def _ensure_terminal_guard(self, job_id: str, current_state: str) -> None:
        """Raise :class:`ConflictError` if the job is already terminal.

        Idempotency: a completed/failed/cancelled job must not be reworked.
        """
        if is_terminal(current_state):
            raise ConflictError(
                message=f"Job {job_id} is already in terminal state '{current_state}'",
                details={"job_id": job_id, "state": current_state},
            )


@celery_app.task(
    bind=True,
    name="app.workers.tasks.analyze_page",
    base=ColorizationTask,
    queue="WORKER_CPU_QUEUES",
    acks_late=True,
    reject_on_worker_lost=True,
)
def analyze_page(self: Task, page_id: str, analysis_id: str) -> dict[str, Any]:
    """Analyze a page (CPU).

    Simulates staged analysis progressing 0 to 100. Emits Celery PROGRESS
    events carrying job_id, stage, progress, message, timestamp. Idempotent:
    when the job is already completed the task returns without duplicating
    work.

    Args:
        page_id: Serializable page identifier.
        analysis_id: Serializable analysis identifier (used as the job id).

    Returns:
        A JSON-serializable dict with analysis result metadata.
    """
    job_id = analysis_id
    task_id = self.request.id

    # Idempotency: check current job state before doing any work.
    try:
        job = asyncio.run(_fetch_job(job_id))
    except Exception as exc:  # pragma: no cover - infra failure path
        raise InternalError(
            message="Failed to read job state",
            details={"job_id": job_id, "error": str(exc)},
        ) from exc

    if job is None:
        raise NotFoundError(
            message=f"Job {job_id} not found",
            details={"job_id": job_id},
        )

    current_state = getattr(job, "estado", "pending")
    if is_terminal(current_state):
        return {
            "job_id": job_id,
            "status": "skipped",
            "reason": f"Job already in terminal state '{current_state}'",
            "state": current_state,
            "task_id": task_id,
        }

    if not is_valid_transition(current_state, "preprocessing"):
        raise ConflictError(
            message=f"Cannot analyze job {job_id} from state '{current_state}'",
            details={"job_id": job_id, "state": current_state},
        )

    # Mark the job as actively preprocessing.
    try:
        asyncio.run(
            _update_job(
                job_id,
                estado="preprocessing",
                progreso=0,
                mensaje="Starting analysis",
                parametros={"page_id": page_id, "analysis_id": analysis_id},
            )
        )
    except Exception as exc:  # pragma: no cover - infra failure path
        raise InternalError(
            message="Failed to initialize job progress",
            details={"job_id": job_id, "error": str(exc)},
        ) from exc

    progress = 0
    total_stages = len(ANALYZE_STAGES)
    stage_results: list[dict[str, Any]] = []

    try:
        for index, (stage, duration, message) in enumerate(ANALYZE_STAGES, start=1):
            _simulate_stage(duration)
            progress = int(round(index / total_stages * 100))
            _record_progress(
                self,
                job_id=job_id,
                stage=stage,
                progress=progress,
                message=message,
            )
            stage_results.append(
                {
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                    "timestamp": _now_iso(),
                }
            )

            # Persist progress after each stage so workers can recover.
            try:
                asyncio.run(
                    _update_job(
                        job_id,
                        estado="preprocessing",
                        progreso=progress,
                        mensaje=message,
                    )
                )
            except Exception as exc:  # pragma: no cover - infra failure path
                raise InternalError(
                    message="Failed to persist progress",
                    details={"job_id": job_id, "stage": stage, "error": str(exc)},
                ) from exc

        # Transition to completed.
        try:
            asyncio.run(
                _update_job(
                    job_id,
                    estado="completed",
                    progreso=100,
                    mensaje="Analysis completed",
                )
            )
        except Exception as exc:  # pragma: no cover - infra failure path
            raise InternalError(
                message="Failed to mark job completed",
                details={"job_id": job_id, "error": str(exc)},
            ) from exc

        result: dict[str, Any] = {
            "job_id": job_id,
            "status": "completed",
            "state": "completed",
            "progress": 100,
            "page_id": page_id,
            "analysis_id": analysis_id,
            "stages": stage_results,
            "task_id": task_id,
            "finished_at": _now_iso(),
        }
        return result

    except ConflictError:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected failure path
        try:
            asyncio.run(
                _update_job(
                    job_id,
                    estado="failed",
                    mensaje=f"Analysis failed: {exc}",
                )
            )
        except Exception:  # pragma: no cover - best-effort failure record
            pass
        raise InternalError(
            message="Analysis failed",
            details={"job_id": job_id, "error": str(exc)},
        ) from exc


@celery_app.task(
    bind=True,
    name="app.workers.tasks.colorize_page",
    base=ColorizationTask,
    queue="WORKER_GPU_QUEUES",
    acks_late=True,
    reject_on_worker_lost=True,
)
def colorize_page(
    self: Task,
    job_id: str,
    analysis_id: str,
    palette: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Colorize a page conditioned on an analysis (GPU).

    Simulates staged colorization progressing 0 to 100, records simulated
    VRAM/duration per stage, and returns result path and model version.
    Idempotent: when the job is already completed the task returns without
    regenerating artifacts.

    Args:
        job_id: Serializable colorization job identifier.
        analysis_id: Serializable analysis identifier the colorization is
            conditioned on.
        palette: Optional color palette parameters (JSON-serializable).

    Returns:
        A JSON-serializable dict with result path and model version.
    """
    task_id = self.request.id

    # Idempotency: check current job state before doing any work.
    try:
        job = asyncio.run(_fetch_job(job_id))
    except Exception as exc:  # pragma: no cover - infra failure path
        raise InternalError(
            message="Failed to read job state",
            details={"job_id": job_id, "error": str(exc)},
        ) from exc

    if job is None:
        raise NotFoundError(
            message=f"Job {job_id} not found",
            details={"job_id": job_id},
        )

    current_state = getattr(job, "estado", "pending")
    if is_terminal(current_state):
        return {
            "job_id": job_id,
            "status": "skipped",
            "reason": f"Job already in terminal state '{current_state}'",
            "state": current_state,
            "task_id": task_id,
        }

    if not is_valid_transition(current_state, "colorizing"):
        raise ConflictError(
            message=f"Cannot colorize job {job_id} from state '{current_state}'",
            details={"job_id": job_id, "state": current_state},
        )

    # Mark the job as actively colorizing.
    try:
        asyncio.run(
            _update_job(
                job_id,
                estado="colorizing",
                progreso=0,
                mensaje="Starting colorization",
                parametros={
                    "analysis_id": analysis_id,
                    "palette": palette or {},
                },
            )
        )
    except Exception as exc:  # pragma: no cover - infra failure path
        raise InternalError(
            message="Failed to initialize job progress",
            details={"job_id": job_id, "error": str(exc)},
        ) from exc

    # Simulated GPU metrics recorded per execution (S8-aligned).
    simulated_vram_mb = 2048
    simulated_duration_s = 0
    stage_results: list[dict[str, Any]] = []
    progress = 0
    total_stages = len(COLORIZE_STAGES)

    try:
        for index, (stage, duration, message) in enumerate(COLORIZE_STAGES, start=1):
            _simulate_stage(duration)
            simulated_duration_s += duration
            progress = int(round(index / total_stages * 100))
            _record_progress(
                self,
                job_id=job_id,
                stage=stage,
                progress=progress,
                message=message,
            )
            stage_results.append(
                {
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                    "timestamp": _now_iso(),
                    "vram_mb": simulated_vram_mb,
                }
            )

            # Persist progress after each stage for recovery.
            try:
                asyncio.run(
                    _update_job(
                        job_id,
                        estado="colorizing",
                        progreso=progress,
                        mensaje=message,
                    )
                )
            except Exception as exc:  # pragma: no cover - infra failure path
                raise InternalError(
                    message="Failed to persist progress",
                    details={"job_id": job_id, "stage": stage, "error": str(exc)},
                ) from exc

        result_path = f"/data/results/{job_id}.png"
        model_version = "manga-colorizer-v1"

        # Transition to completed with result metadata.
        try:
            asyncio.run(
                _update_job(
                    job_id,
                    estado="completed",
                    progreso=100,
                    mensaje="Colorization completed",
                    ruta_resultado=result_path,
                    version_modelo=model_version,
                )
            )
        except Exception as exc:  # pragma: no cover - infra failure path
            raise InternalError(
                message="Failed to mark job completed",
                details={"job_id": job_id, "error": str(exc)},
            ) from exc

        result: dict[str, Any] = {
            "job_id": job_id,
            "status": "completed",
            "state": "completed",
            "progress": 100,
            "analysis_id": analysis_id,
            "ruta_resultado": result_path,
            "version_modelo": model_version,
            "vram_mb": simulated_vram_mb,
            "duration_s": simulated_duration_s,
            "palette": palette or {},
            "stages": stage_results,
            "task_id": task_id,
            "finished_at": _now_iso(),
        }
        return result

    except ConflictError:
        raise
    except AppError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected failure path
        try:
            asyncio.run(
                _update_job(
                    job_id,
                    estado="failed",
                    mensaje=f"Colorization failed: {exc}",
                )
            )
        except Exception:  # pragma: no cover - best-effort failure record
            pass
        raise InternalError(
            message="Colorization failed",
            details={"job_id": job_id, "error": str(exc)},
        ) from exc
