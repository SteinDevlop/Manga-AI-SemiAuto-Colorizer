"""RED/GREEN tests for P1 repositories (T4).

Verifies that each repository class exposes the expected CRUD methods.
No database connection required — only class introspection.
"""

from app.modules.character_analysis.repositories import (
    CharacterAppearanceRepository,
    CharacterRepository,
)
from app.modules.character_configuration.repositories import (
    CharacterAttributeRepository,
    CharacterPaletteRepository,
)
from app.modules.character_memory.repositories import ModelManifestRepository
from app.modules.colorization.repositories import (
    ColorizationJobRepository,
    MaskArtifactRepository,
)
from app.modules.page_analysis.repositories import (
    AnalysisRepository,
    PageRepository,
    PanelRepository,
)
from app.modules.projects.repositories import ProjectRepository

EXPECTED_METHODS = {"get", "list", "create", "update", "delete", "exists"}


def test_project_repository_has_crud_methods():
    """ProjectRepository must expose get, list, create, update, delete, exists."""
    methods = {name for name in dir(ProjectRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)
    assert "exists_by_name" in methods


def test_page_repository_has_crud_methods():
    """PageRepository must expose CRUD methods plus list-by-project filter."""
    methods = {name for name in dir(PageRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)


def test_panel_repository_has_crud_methods():
    """PanelRepository must expose CRUD methods plus list-by-page filter."""
    methods = {name for name in dir(PanelRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)


def test_analysis_repository_has_crud_methods():
    """AnalysisRepository must expose CRUD methods (no list: page_id is unique) plus get_by_page_id."""
    methods = {name for name in dir(AnalysisRepository) if not name.startswith("_")}
    expected_without_list = EXPECTED_METHODS - {"list"}
    assert expected_without_list.issubset(methods)
    assert "get_by_page_id" in methods


def test_character_repository_has_crud_methods():
    """CharacterRepository must expose CRUD methods."""
    methods = {name for name in dir(CharacterRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)


def test_character_appearance_repository_has_crud_methods():
    """CharacterAppearanceRepository exposes all identity use-case query/update ports."""
    methods = {name for name in dir(CharacterAppearanceRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)
    assert {"list_by_page", "list_by_character", "update_character"}.issubset(methods)


def test_character_attribute_repository_has_crud_methods():
    """CharacterAttributeRepository exposes CRUD and use-case lookup ports."""
    methods = {name for name in dir(CharacterAttributeRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)
    assert "get_by_character_and_name" in methods


def test_character_palette_repository_has_crud_methods():
    """CharacterPaletteRepository exposes CRUD and use-case lookup ports."""
    methods = {name for name in dir(CharacterPaletteRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)
    assert "get_by_character_and_name" in methods


def test_character_memory_repository_has_memory_lookup():
    from app.modules.character_memory.repositories import CharacterMemoryRepository
    assert "get_by_character" in dir(CharacterMemoryRepository)


def test_mask_artifact_repository_has_crud_methods():
    """MaskArtifactRepository exposes CRUD and mask use-case lookup ports."""
    methods = {name for name in dir(MaskArtifactRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)
    assert "list_by_appearance" in methods


def test_colorization_job_repository_has_crud_methods():
    """ColorizationJobRepository must expose CRUD methods plus list filters."""
    methods = {name for name in dir(ColorizationJobRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)


def test_model_manifest_repository_has_crud_methods():
    """ModelManifestRepository must expose CRUD methods."""
    methods = {name for name in dir(ModelManifestRepository) if not name.startswith("_")}
    assert EXPECTED_METHODS.issubset(methods)


def test_repository_methods_are_async():
    """Repository CRUD methods must be async coroutines."""
    import asyncio

    repos = [
        (ProjectRepository, EXPECTED_METHODS),
        (PageRepository, EXPECTED_METHODS),
        (PanelRepository, EXPECTED_METHODS),
        (AnalysisRepository, EXPECTED_METHODS - {"list"}),
        (CharacterRepository, EXPECTED_METHODS),
        (CharacterAppearanceRepository, EXPECTED_METHODS),
        (CharacterAttributeRepository, EXPECTED_METHODS),
        (CharacterPaletteRepository, EXPECTED_METHODS),
        (MaskArtifactRepository, EXPECTED_METHODS),
        (ColorizationJobRepository, EXPECTED_METHODS),
        (ModelManifestRepository, EXPECTED_METHODS),
    ]
    for repo_cls, expected in repos:
        for method_name in expected:
            method = getattr(repo_cls, method_name)
            assert asyncio.iscoroutinefunction(
                method
            ), f"{repo_cls.__name__}.{method_name} must be async"
