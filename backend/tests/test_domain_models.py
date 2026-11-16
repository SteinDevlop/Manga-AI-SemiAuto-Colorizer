"""RED/GREEN tests for P1 domain models (T2).

These tests verify that SQLAlchemy 2.0 models are declared with the
expected tables, columns, foreign keys, and indexes. No database
connection is required — only mapper introspection.
"""

from app.infrastructure.database.base import Base
from sqlalchemy import inspect


def test_base_metadata_registers_all_tables():
    """All 11 domain entities must be registered in Base.metadata."""
    expected = {
        "projects",
        "pages",
        "panels",
        "analyses",
        "characters",
        "character_appearances",
        "character_attributes",
        "character_palettes",
        "mask_artifacts",
        "colorization_jobs",
        "model_manifests",
    }
    registered = set(Base.metadata.tables.keys())
    missing = expected - registered
    assert not missing, f"Missing tables: {sorted(missing)}"


def test_project_has_expected_columns():
    """Project model must have nombre and descripcion columns."""
    from app.modules.projects.models import Project

    mapper = inspect(Project)
    columns = {c.name for c in mapper.columns}
    assert {"id", "nombre", "descripcion", "created_at", "updated_at"}.issubset(columns)


def test_page_has_project_foreign_key():
    """Page must reference projects.id as a non-null indexed FK."""
    from app.modules.projects.models import Page

    mapper = inspect(Page)
    project_fks = [
        fk for fk in mapper.local_table.foreign_keys if fk.column.table.name == "projects"
    ]
    assert len(project_fks) == 1, "Page must have exactly one FK to projects"
    assert project_fks[0].column.name == "id"
    assert not project_fks[0].column.nullable


def test_analysis_has_unique_page_foreign_key():
    """Analysis must have a unique FK to pages.id (one analysis per page)."""
    from app.modules.page_analysis.models import Analysis

    mapper = inspect(Analysis)
    page_fks = [fk for fk in mapper.local_table.foreign_keys if fk.column.table.name == "pages"]
    assert len(page_fks) == 1, "Analysis must have exactly one FK to pages"
    assert not page_fks[0].column.nullable

    # page_id column must be unique
    page_id_col = [c for c in mapper.columns if c.name == "page_id"][0]
    assert page_id_col.unique, "Analysis.page_id must be unique"


def test_character_appearance_has_three_foreign_keys():
    """CharacterAppearance references pages, characters, and panels."""
    from app.modules.character_analysis.models import CharacterAppearance

    mapper = inspect(CharacterAppearance)
    fk_tables = {fk.column.table.name for fk in mapper.local_table.foreign_keys}
    assert {"pages", "characters", "panels"}.issubset(fk_tables)


def test_mask_artifact_no_binary_in_postgres():
    """MaskArtifact must store file paths, not binary blobs."""
    from app.modules.colorization.models import MaskArtifact

    mapper = inspect(MaskArtifact)
    columns = {c.name for c in mapper.columns}
    assert "ruta_archivo" in columns
    assert "hash_sha256" in columns
    # No LargeBinary or BLOB columns
    for col in mapper.columns:
        assert "LargeBinary" not in str(col.type), (
            f"Column {col.name} must not store binary data in PostgreSQL"
        )


def test_all_models_inherit_common_columns():
    """Every model must inherit id, created_at, updated_at from Base."""
    from app.modules.character_analysis.models import Character, CharacterAppearance
    from app.modules.character_configuration.models import (
        CharacterAttribute,
        CharacterPalette,
    )
    from app.modules.character_memory.models import ModelManifest
    from app.modules.colorization.models import ColorizationJob, MaskArtifact
    from app.modules.page_analysis.models import Analysis, Panel
    from app.modules.projects.models import Page, Project

    models = [
        Project,
        Page,
        Panel,
        Analysis,
        Character,
        CharacterAppearance,
        CharacterAttribute,
        CharacterPalette,
        MaskArtifact,
        ColorizationJob,
        ModelManifest,
    ]
    for model in models:
        mapper = inspect(model)
        columns = {c.name for c in mapper.columns}
        assert {"id", "created_at", "updated_at"}.issubset(columns), (
            f"{model.__name__} missing common columns"
        )
