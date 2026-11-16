"""RED/GREEN tests for P3 job states (S1).

Verifies state machine transitions for colorization jobs. No database
required — only pure functions from app.modules.colorization.states.
"""


from app.modules.colorization.states import (
    ACTIVE_STATES,
    ALLOWED_TRANSITIONS,
    JOB_STATES,
    TERMINAL_STATES,
    is_active,
    is_terminal,
    is_valid_transition,
)


def test_job_states_defined():
    """Todos los estados esperados deben estar definidos."""
    expected = {
        "pending", "preprocessing", "colorizing", "refining",
        "completed", "failed", "cancelled",
    }
    assert set(JOB_STATES) == expected


def test_terminal_states():
    """Los estados terminales deben ser completed, failed, cancelled."""
    assert set(TERMINAL_STATES) == {"completed", "failed", "cancelled"}


def test_active_states():
    """Los estados activos deben ser preprocessing, colorizing, refining."""
    assert set(ACTIVE_STATES) == {"preprocessing", "colorizing", "refining"}


def test_is_terminal():
    """is_terminal debe retornar True solo para estados terminales."""
    assert is_terminal("completed") is True
    assert is_terminal("failed") is True
    assert is_terminal("cancelled") is True
    assert is_terminal("pending") is False
    assert is_terminal("colorizing") is False


def test_is_active():
    """is_active debe retornar True solo para estados de procesamiento."""
    assert is_active("preprocessing") is True
    assert is_active("colorizing") is True
    assert is_active("refining") is True
    assert is_active("pending") is False
    assert is_active("completed") is False


def test_is_valid_transition_pending_to_preprocessing():
    """pending -> preprocessing debe ser válido."""
    assert is_valid_transition("pending", "preprocessing") is True


def test_is_valid_transition_pending_to_completed_invalid():
    """pending -> completed directamente no debe ser válido."""
    assert is_valid_transition("pending", "completed") is False


def test_is_valid_transition_colorizing_to_completed():
    """colorizing -> completed debe ser válido."""
    assert is_valid_transition("colorizing", "completed") is True


def test_is_valid_transition_terminal_no_outgoing():
    """Desde un estado terminal (excepto failed->pending reintento) no debe haber transiciones."""
    for terminal in ("completed", "cancelled"):
        for dest in JOB_STATES:
            assert is_valid_transition(terminal, dest) is False


def test_is_valid_transition_unknown_state():
    """Estados desconocidos no deben tener transiciones válidas."""
    assert is_valid_transition("unknown", "pending") is False
    assert is_valid_transition("pending", "unknown") is False


def test_failed_can_retry_to_pending():
    """failed -> pending debe ser válido (reintento explícito)."""
    assert is_valid_transition("failed", "pending") is True


def test_all_transitions_are_in_allowed_map():
    """Cada transición en ALLOWED_TRANSITIONS debe referenciar estados válidos."""
    for origin, destinations in ALLOWED_TRANSITIONS.items():
        assert origin in JOB_STATES, f"Estado origen desconocido: {origin}"
        for dest in destinations:
            assert dest in JOB_STATES, f"Estado destino desconocido: {dest}"
