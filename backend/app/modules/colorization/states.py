"""Estados y transiciones permitidas para trabajos de colorización.

Los estados son persistentes y auditable. Cada transición válida está
registrada para que ningún caso de uso ni worker pueda avanzar un trabajo
a un estado no permitido.
"""

from __future__ import annotations

from typing import Final

#: Estados públicos del ciclo de vida de un trabajo de colorización.
JOB_STATES: Final[tuple[str, ...]] = (
    "pending",
    "preprocessing",
    "colorizing",
    "refining",
    "completed",
    "failed",
    "cancelled",
)

#: Estados transitorios (el trabajo está siendo procesado).
ACTIVE_STATES: Final[tuple[str, ...]] = (
    "preprocessing",
    "colorizing",
    "refining",
)

#: Estados terminales (no se admiten más transiciones).
TERMINAL_STATES: Final[tuple[str, ...]] = (
    "completed",
    "failed",
    "cancelled",
)

#: Transiciones permitidas: estado_origen -> conjunto de estados destino.
ALLOWED_TRANSITIONS: Final[dict[str, set[str]]] = {
    "pending": {"preprocessing", "colorizing", "cancelled"},
    "preprocessing": {"colorizing", "failed", "cancelled"},
    "colorizing": {"refining", "completed", "failed", "cancelled"},
    "refining": {"completed", "failed"},
    "completed": set(),
    "failed": {"pending"},  # reintento explícito
    "cancelled": set(),
}


def is_valid_transition(from_state: str, to_state: str) -> bool:
    """Retorna True si la transición de estado es permitida."""
    if from_state not in JOB_STATES or to_state not in JOB_STATES:
        return False
    return to_state in ALLOWED_TRANSITIONS.get(from_state, set())


def is_terminal(state: str) -> bool:
    """Retorna True si el estado es terminal."""
    return state in TERMINAL_STATES


def is_active(state: str) -> bool:
    """Retorna True si el estado indica procesamiento activo."""
    return state in ACTIVE_STATES
