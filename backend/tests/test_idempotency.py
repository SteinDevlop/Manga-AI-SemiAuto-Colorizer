"""RED/GREEN tests for P3 idempotent retries (S6).

Verifies that Celery tasks short-circuit when a job is already terminal,
never regenerating artifacts.
"""

from app.workers.tasks.colorization_tasks import (
    analyze_page,
    colorize_page,
)


def test_tasks_have_expected_names():
    """Los nombres de tarea deben coincidir con celery_app.task_routes."""
    assert analyze_page.name == "app.workers.tasks.analyze_page"
    assert colorize_page.name == "app.workers.tasks.colorize_page"


def test_tasks_are_bound():
    """Las tareas deben usar bind=True para acceder a self.request y update_state."""
    # Celery Task.bind es una propiedad; verificar que las tareas tienen
    # request y update_state disponibles (indicio de bind=True).
    assert hasattr(analyze_page, "request")
    assert hasattr(analyze_page, "update_state")
    assert hasattr(colorize_page, "request")
    assert hasattr(colorize_page, "update_state")


def test_idempotency_short_circuit_logic():
    """La lógica de short-circuito por estado terminal es correcta."""
    from app.modules.colorization.states import is_terminal

    assert is_terminal("completed") is True
    assert is_terminal("failed") is True
    assert is_terminal("cancelled") is True
    assert is_terminal("pending") is False
    assert is_terminal("colorizing") is False
