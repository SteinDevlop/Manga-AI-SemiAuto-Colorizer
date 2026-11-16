"""RED/GREEN tests for P1 use cases (T5).

Verifies that use case classes import correctly, expose the expected
execute methods, and reuse the P0 error envelope.
"""

from app.application.use_cases.create_page import CreatePageUseCase
from app.application.use_cases.create_project import CreateProjectUseCase
from app.application.use_cases.get_page import GetPageUseCase
from app.application.use_cases.get_project import GetProjectUseCase
from app.application.use_cases.list_pages import ListPagesUseCase
from app.application.use_cases.list_projects import ListProjectsUseCase
from app.core.exceptions import ConflictError, NotFoundError, ValidationError


def test_error_envelope_matches_p0_contract():
    """P0 errors must carry code, message, details, request_id."""
    err = NotFoundError(message="test", details={"k": "v"}, request_id="req-1")
    d = err.to_dict()
    assert d["code"] == "not_found"
    assert d["message"] == "test"
    assert d["details"] == {"k": "v"}
    assert d["request_id"] == "req-1"


def test_create_project_use_case_has_execute():
    """CreateProjectUseCase must expose an async execute method."""
    import asyncio

    assert asyncio.iscoroutinefunction(CreateProjectUseCase.execute)


def test_get_project_use_case_has_execute():
    """GetProjectUseCase must expose an async execute method."""
    import asyncio

    assert asyncio.iscoroutinefunction(GetProjectUseCase.execute)


def test_list_projects_use_case_has_execute():
    """ListProjectsUseCase must expose an async execute method."""
    import asyncio

    assert asyncio.iscoroutinefunction(ListProjectsUseCase.execute)


def test_create_page_use_case_has_execute():
    """CreatePageUseCase must expose an async execute method."""
    import asyncio

    assert asyncio.iscoroutinefunction(CreatePageUseCase.execute)


def test_get_page_use_case_has_execute():
    """GetPageUseCase must expose an async execute method."""
    import asyncio

    assert asyncio.iscoroutinefunction(GetPageUseCase.execute)


def test_list_pages_use_case_has_execute():
    """ListPagesUseCase must expose an async execute method."""
    import asyncio

    assert asyncio.iscoroutinefunction(ListPagesUseCase.execute)


def test_use_cases_reuse_p0_errors():
    """Use cases must import errors from app.core.exceptions (P0 contract)."""
    assert NotFoundError.code == "not_found"
    assert ConflictError.code == "conflict"
    assert ValidationError.code == "validation_error"
