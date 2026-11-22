"""Garantiza que las dependencias declaradas coinciden con las que el código usa.

Evita regresiones como importar ``cryptography`` sin declararla, o tener
``requirements.txt`` y ``pyproject.toml`` desincronizados.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

# Imports opcionales: se cargan de forma diferida y solo con el extra ``ml``,
# o pertenecen al paquete local ``ml/`` (fuera de backend/).
OPTIONAL_IMPORTS = {"torch", "onnxruntime", "models"}
# Dependencias transitivas garantizadas por un paquete declarado.
TRANSITIVE = {"starlette": "fastapi"}


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_requirement(line: str) -> tuple[str, str]:
    m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(?:\[[^\]]*\])?\s*(.*)$", line.strip())
    assert m, f"Requisito ilegible: {line!r}"
    return _norm(m.group(1)), m.group(2).strip()


def _requirements_txt() -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (BACKEND / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            name, spec = _parse_requirement(line)
            out[name] = spec
    return out


def _pyproject_deps() -> dict[str, str]:
    data = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    return dict(_parse_requirement(d) for d in data["project"]["dependencies"])


def test_requirements_txt_matches_pyproject_runtime_dependencies():
    req, proj = _requirements_txt(), _pyproject_deps()
    assert req == proj, (
        "requirements.txt y pyproject.toml difieren. "
        f"Solo en requirements: {sorted(set(req) - set(proj))}; "
        f"solo en pyproject: {sorted(set(proj) - set(req))}; "
        f"versiones distintas: {sorted(k for k in set(req) & set(proj) if req[k] != proj[k])}"
    )


def test_runtime_dependencies_are_pinned():
    unpinned = [n for n, spec in _requirements_txt().items() if not spec.startswith("==")]
    assert not unpinned, f"Dependencias sin versión fija: {unpinned}"


def _third_party_imports() -> dict[str, set[str]]:
    stdlib = set(sys.stdlib_module_names)
    found: dict[str, set[str]] = {}
    for path in (BACKEND / "app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module]
            else:
                continue
            for mod in mods:
                top = mod.split(".")[0]
                if top not in stdlib and top != "app":
                    found.setdefault(top, set()).add(str(path.relative_to(BACKEND)))
    return found


def test_every_third_party_import_in_app_is_declared():
    declared = set(_pyproject_deps())
    dist_of = packages_distributions()  # import name -> [distribuciones]
    missing: list[str] = []
    for top, files in sorted(_third_party_imports().items()):
        if top in OPTIONAL_IMPORTS:
            continue
        if top in TRANSITIVE:
            assert TRANSITIVE[top] in declared
            continue
        dists = {_norm(d) for d in dist_of.get(top, [])}
        if not dists & declared:
            missing.append(f"{top} (usado en {sorted(files)[:2]})")
    assert not missing, f"Imports de terceros sin declarar en pyproject/requirements: {missing}"


def test_alembic_runtime_driver_is_declared():
    """alembic/env.py convierte la URL a psycopg2: debe estar instalable."""
    env = (BACKEND / "alembic" / "env.py").read_text(encoding="utf-8")
    if "psycopg2" in env:
        assert "psycopg2-binary" in _pyproject_deps()
