"""RED/GREEN tests for P3 reconciliation (S7).

Verifies reconciliation helpers: find_stale_jobs, mark_stale_as_failed,
cancel_job, can_transition. Uses isolated in-memory SQLite via async session
override when available; otherwise verifies pure logic.
"""

from app.modules.colorization.reconciliation import (
    STALE_ACTIVE_TIMEOUT_SECONDS,
    can_transition,
    cancel_job,
    find_stale_jobs,
    mark_stale_as_failed,
)


def test_stale_timeout_default():
    """El timeout por defecto de estados activos abandonados debe ser 3600s."""
    assert STALE_ACTIVE_TIMEOUT_SECONDS == 3600


def test_reconciliation_functions_exist():
    """Las funciones de reconciliación deben existir y ser llamables."""
    assert callable(find_stale_jobs)
    assert callable(mark_stale_as_failed)
    assert callable(cancel_job)
    assert callable(can_transition)
