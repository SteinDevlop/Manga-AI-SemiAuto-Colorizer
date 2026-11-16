"""Real character matcher adapter (placeholder).

Implements the ``CharacterMatcher`` protocol. Attempts to load a real
matching model; when the model is unavailable it records the error and
every subsequent :meth:`match` call raises :class:`ModelUnavailableError`
with a clear message. No heavy inference is executed here (the real model
lands in P8/future).
"""

from __future__ import annotations

from typing import TypedDict

from . import ModelUnavailableError


class IdentityProposal(TypedDict):
    """Serialized identity-matching proposal."""

    apariciones: list[str]
    confianza_identidad: float
    nombre_sugerido: str


class RealCharacterMatcher:
    """Real placeholder implementation of :class:`CharacterMatcher`.

    The constructor calls :meth:`load_model`, which attempts to load the
    real matching model. When loading fails (missing weights, no GPU,
    etc.) the error is stored and every later :meth:`match` call raises
    :class:`ModelUnavailableError` with a clear message.
    """

    MODEL_NAME: str = "character-matcher"
    MODEL_PATH: str = "models/character_matcher.pt"

    def __init__(self) -> None:
        self._model: object | None = None
        self._load_error: str | None = None
        self._loaded: bool = False
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the real matching model.

        Returns:
            ``True`` when the model was loaded, ``False`` otherwise. On
            failure the error is stored and no exception is raised here;
            subsequent :meth:`match` calls raise
            :class:`ModelUnavailableError`.
        """
        try:
            self._load_real_model()
        except Exception as exc:  # noqa: BLE001 - report any load failure
            self._loaded = False
            self._model = None
            self._load_error = f"{type(exc).__name__}: {exc}"
            return False
        self._loaded = True
        return True

    def _load_real_model(self) -> None:
        """Attempt to load the real model weights (placeholder).

        No real model exists yet in this phase, so this intentionally
        raises :class:`FileNotFoundError` to surface that the weights are
        missing instead of failing silently.
        """
        raise FileNotFoundError(
            f"Character matcher weights not found at {self.MODEL_PATH}"
        )

    def _ensure_loaded(self) -> None:
        if not self._loaded or self._model is None:
            raise ModelUnavailableError(
                self.MODEL_NAME,
                self._load_error or "model not loaded",
            )

    def match(self, appearances: list[dict]) -> list[IdentityProposal]:
        """Return identity proposals for the given appearances.

        Args:
            appearances: Character appearance detections.

        Returns:
            A list of identity-matching proposals.

        Raises:
            ModelUnavailableError: When the real model is not available.
        """
        self._ensure_loaded()
        del appearances  # placeholder: no inference yet
        return []
