"""Contratos (Protocols) del motor de IA desacoplado.

Define las interfaces que los casos de uso invocan sin acoplarse a
implementaciones concretas de modelos (ADR-004, ADR-007). Los modelos
concretos se integran mediante adaptadores que implementan estos
Protocolos, permitiendo sustituir detección, segmentación y matching
sin cambiar los casos de uso.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CharacterDetector(Protocol):
    """Detecta apariciones de personaje en una imagen de página o panel."""

    def detect(
        self,
        image_path: str,
        *,
        min_confidence: float = 0.0,
    ) -> list[dict]:
        """Devuelve lista de detecciones con bounding box, confianza y etiqueta.

        Cada detección: {"x", "y", "ancho", "alto", "confianza", "etiqueta"}.
        """


@runtime_checkable
class PanelDetector(Protocol):
    """Detecta paneles/viñetas en una página de manga."""

    def detect(
        self,
        image_path: str,
        *,
        min_confidence: float = 0.0,
    ) -> list[dict]:
        """Devuelve lista de paneles con bounding box, orden y confianza.

        Cada panel: {"numero_orden", "x", "y", "ancho", "alto", "confianza"}.
        """


@runtime_checkable
class Segmenter(Protocol):
    """Segmenta regiones de personaje/fondo para extraer máscaras."""

    def segment(
        self,
        image_path: str,
        *,
        regions: list[dict],
    ) -> list[dict]:
        """Devuelve máscaras para cada región solicitada.

        Cada máscara: {"region_id", "ruta_archivo", "hash_sha256", "ancho",
        "alto", "tipo_mascara"}.
        """


@runtime_checkable
class CharacterMatcher(Protocol):
    """Agrupa apariciones de personaje en identidades estables."""

    def match(
        self,
        appearances: list[dict],
    ) -> list[dict]:
        """Devuelve propuestas de identidad con confianza de matching.

        Cada propuesta: {"apariciones": [ids], "confianza_identidad",
        "nombre_sugerido"}.
        """


@runtime_checkable
class ColorizationEngine(Protocol):
    """Ejecuta colorización condicionada (adaptador mock en esta fase)."""

    def colorize(
        self,
        *,
        image_path: str,
        mask_references: list[str],
        palette: dict,
    ) -> dict:
        """Devuelve {"ruta_resultado", "version_modelo", "parametros"}.

        No ejecuta inferencia pesada real en esta fase (P8 integra el modelo).
        """
