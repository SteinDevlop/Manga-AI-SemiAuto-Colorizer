"""RED/GREEN tests for P3 progress events (S3).

Verifies that progress event payloads contain the required fields:
job_id, stage, progress, message, timestamp.
"""

import re

from app.workers.tasks.colorization_tasks import (
    _progress_event,
)


def test_progress_event_has_required_fields():
    """Cada evento de progreso debe tener job_id, stage, progress, message, timestamp."""
    event = _progress_event(job_id="job-123", stage="preprocessing", progress=25, message="Detectando paneles")
    required = {"job_id", "stage", "progress", "message", "timestamp"}
    assert required.issubset(set(event.keys()))
    assert event["job_id"] == "job-123"
    assert event["stage"] == "preprocessing"
    assert event["progress"] == 25
    assert event["message"] == "Detectando paneles"
    # timestamp debe ser ISO-8601 parseable
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", event["timestamp"])


def test_progress_event_progress_range():
    """progress debe estar entre 0 y 100."""
    event = _progress_event(job_id="job-1", stage="colorizing", progress=0, message="Iniciando")
    assert event["progress"] == 0
    event = _progress_event(job_id="job-1", stage="completed", progress=100, message="Listo")
    assert event["progress"] == 100


def test_progress_event_task_id_when_provided():
    """task_id debe incluirse cuando se pasa explícitamente."""
    event = _progress_event(
        job_id="job-1", stage="preprocessing", progress=10,
        message="Etapa 1", task_id="task-abc",
    )
    assert "task_id" in event
    assert event["task_id"] == "task-abc"
    assert isinstance(event["task_id"], str)
    assert len(event["task_id"]) > 0


def test_progress_event_task_id_optional():
    """task_id es opcional y no debe estar presente si no se pasa."""
    event = _progress_event(job_id="job-1", stage="preprocessing", progress=10, message="Etapa 1")
    assert "task_id" not in event
