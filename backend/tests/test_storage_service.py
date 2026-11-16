"""RED/GREEN tests for P2 storage service (T1).

Verifies StorageService save/read/exists/path/delete/list_by_type
behavior using a temporary isolated directory. No database required.
"""

import hashlib
import tempfile
from pathlib import Path

import pytest
from app.infrastructure.storage.service import StorageService


@pytest.fixture
def tmp_storage():
    with tempfile.TemporaryDirectory() as tmp:
        yield StorageService(tmp)


def test_save_returns_artifact_metadata(tmp_storage):
    """Guardar un archivo debe retornar artifact_id, hash, tamaño y ruta."""
    content = b"test image content"
    source = Path(tmp_storage.root) / "source.png"
    source.write_bytes(content)

    result = tmp_storage.save(str(source), "original", "manga_page.png")

    assert "artifact_id" in result
    assert result["tipo"] == "original"
    assert result["hash_sha256"] == hashlib.sha256(content).hexdigest()
    assert result["tamano_bytes"] == len(content)
    assert result["nombre_original"] == "manga_page.png"
    assert Path(result["ruta_archivo"]).exists()


def test_save_generates_internal_name_not_client_name(tmp_storage):
    """El nombre interno no debe ser el nombre proporcionado por el cliente."""
    source = Path(tmp_storage.root) / "source.png"
    source.write_bytes(b"data")

    result = tmp_storage.save(str(source), "mask", "../../../evil.png")

    saved_path = Path(result["ruta_archivo"])
    assert saved_path.name != "../../../evil.png"
    assert "evil" not in saved_path.name
    assert saved_path.suffix in (".png", ".bin")


def test_read_returns_saved_content(tmp_storage):
    """Leer un artefacto debe retornar el contenido guardado."""
    content = b"mask data"
    source = Path(tmp_storage.root) / "source.mask"
    source.write_bytes(content)

    result = tmp_storage.save(str(source), "mask", "mask.mask")
    read_back = tmp_storage.read(result["artifact_id"], "mask")

    assert read_back == content


def test_exists_returns_true_for_saved_artifact(tmp_storage):
    """exists debe retornar True para un artefacto guardado."""
    source = Path(tmp_storage.root) / "source.ref"
    source.write_bytes(b"reference data")

    result = tmp_storage.save(str(source), "reference", "ref.png")

    assert tmp_storage.exists(result["artifact_id"], "reference") is True


def test_exists_returns_false_for_missing_artifact(tmp_storage):
    """exists debe retornar False para un artefacto inexistente."""
    assert tmp_storage.exists("00000000-0000-0000-0000-000000000000", "preview") is False


def test_path_returns_existing_file(tmp_storage):
    """path debe retornar la ruta del archivo sin leerlo."""
    source = Path(tmp_storage.root) / "source.result"
    source.write_bytes(b"result")

    result = tmp_storage.save(str(source), "result", "result.png")

    p = tmp_storage.path(result["artifact_id"], "result")
    assert p.exists()
    assert p.read_bytes() == b"result"


def test_delete_removes_artifact(tmp_storage):
    """delete debe eliminar el archivo y retornar True."""
    source = Path(tmp_storage.root) / "source.del"
    source.write_bytes(b"to delete")

    result = tmp_storage.save(str(source), "original", "del.png")

    assert tmp_storage.delete(result["artifact_id"], "original") is True
    assert tmp_storage.exists(result["artifact_id"], "original") is False


def test_delete_returns_false_for_missing(tmp_storage):
    """delete debe retornar False para un artefacto inexistente."""
    assert tmp_storage.delete("00000000-0000-0000-0000-000000000000", "mask") is False


def test_list_by_type_returns_saved_artifacts(tmp_storage):
    """list_by_type debe retornar todos los artefactos de un tipo."""
    for i in range(3):
        source = Path(tmp_storage.root) / f"source_{i}.preview"
        source.write_bytes(f"preview {i}".encode())
        tmp_storage.save(str(source), "preview", f"preview_{i}.png")

    artifacts = tmp_storage.list_by_type("preview")
    assert len(artifacts) == 3
    for a in artifacts:
        assert a["tipo"] == "preview"
        assert "artifact_id" in a
