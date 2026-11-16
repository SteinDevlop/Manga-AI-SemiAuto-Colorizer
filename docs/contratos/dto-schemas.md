# DTO schemas — AI engine contracts

## Source

Derived from arc42.md §5.4 Contrato del motor de IA. The domain invokes capabilities through versioned DTOs and protocol interfaces, never concrete model classes.

## Protocol interfaces (Python conceptual)

```python
from typing import Protocol, List
from uuid import UUID
from datetime import datetime


class CharacterDetection:
    def __init__(
        self,
        panel_id: UUID,
        bbox: List[float],          # [x, y, w, h] normalized 0..1
        confidence: float,
    ):
        ...


class CharacterAppearanceInput:
    def __init__(
        self,
        appearance_id: UUID,
        panel_id: UUID,
        bbox: List[float],
        embedding: List[float],
    ):
        ...


class CharacterIdentityProposal:
    def __init__(
        self,
        character_id: UUID | None,
        appearance_ids: List[UUID],
        confidence: float,
        ambiguous: bool,
    ):
        ...


class RegionRequest:
    def __init__(
        self,
        appearance_id: UUID,
        bbox: List[float],
        mask_artifact_id: UUID | None,
    ):
        ...


class MaskArtifactDTO:
    def __init__(
        self,
        artifact_id: UUID,
        image_path: str,            # resolved through storage service
        bbox: List[float],
    ):
        ...


class ColorizationRequest:
    def __init__(
        self,
        job_id: UUID,
        page_id: UUID,
        original_artifact_id: UUID,
        mask_artifact_ids: List[UUID],
        reference_artifact_ids: List[UUID],
        palette_id: UUID,
        attributes: dict,           # skin, hair, eyes, clothing, accessories
        resolution_profile: str,    # fast / balanced / high_quality
        seed: int | None = None,
    ):
        ...


class ColorizationResult:
    def __init__(
        self,
        result_artifact_id: UUID,
        duration_ms: int,
        vram_peak_mb: int | None,
        metrics: dict,
    ):
        ...


class CharacterDetector(Protocol):
    def detect(self, page_path: str) -> List[CharacterDetection]:
        ...


class CharacterMatcher(Protocol):
    def group(
        self,
        appearances: List[CharacterAppearanceInput]
    ) -> List[CharacterIdentityProposal]:
        ...


class Segmenter(Protocol):
    def segment(
        self,
        image_path: str,
        regions: List[RegionRequest]
    ) -> List[MaskArtifactDTO]:
        ...


class ColorizationEngine(Protocol):
    def colorize(
        self,
        request: ColorizationRequest
    ) -> ColorizationResult:
        ...
```

## Conventions

- DTOs are versioned dataclasses/pydantic models; adding fields is backward compatible, removing or renaming fields requires a new version.
- File paths are resolved through a storage service; models never assume absolute paths.
- All IDs are UUID strings; all timestamps are UTC ISO-8601.
- The AI engine returns plain DTOs, not ORM objects or binary payloads.
