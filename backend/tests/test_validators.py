"""RED/GREEN tests for P2 file validators (T2).

Verifies MIME, size, content-extension, dimension, and safe-name validation
using temporary files. No database required.
"""

import tempfile
from pathlib import Path

import pytest
from app.modules.assets.validators import (
    generate_safe_internal_name,
    validate_content_matches_extension,
    validate_dimensions,
    validate_file_size,
    validate_mime_type,
)


@pytest.fixture
def tmp_files():
    """Crea archivos temporales y retorna rutas."""
    files = {}

    with tempfile.TemporaryDirectory() as tmp:
        # PNG válido (1x1) generado con Pillow cuando está disponible, o
        # magic bytes de PNG como fallback.
        png_path = Path(tmp) / "test.png"
        try:
            from PIL import Image as PilImage

            PilImage.new("RGB", (1, 1), (255, 0, 0)).save(png_path, format="PNG")
        except Exception:
            png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"rest of png")

        # JPEG-like
        jpg_path = Path(tmp) / "test.jpg"
        jpg_path.write_bytes(b"\xff\xd8\xff" + b"rest of jpeg")

        # Text with .png extension (mismatch)
        mismatch_path = Path(tmp) / "mismatch.png"
        mismatch_path.write_bytes(b"this is not a real png")

        # Oversized text file
        big_path = Path(tmp) / "big.png"
        big_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200000)

        files["png"] = str(png_path)
        files["jpg"] = str(jpg_path)
        files["mismatch"] = str(mismatch_path)
        files["big"] = str(big_path)
        yield files


def test_validate_mime_type_accepts_png(tmp_files):
    """validate_mime_type debe aceptar PNG con magic bytes válidos."""
    validate_mime_type(tmp_files["png"], {"image/png"})


def test_validate_mime_type_rejects_wrong_mime(tmp_files):
    """validate_mime_type debe rechazar MIME no permitido."""
    with pytest.raises(Exception):
        validate_mime_type(tmp_files["png"], {"image/jpeg"})


def test_validate_file_size_accepts_under_limit(tmp_files):
    """validate_file_size debe aceptar archivos bajo el límite."""
    validate_file_size(tmp_files["png"], 1000000)


def test_validate_file_size_rejects_over_limit(tmp_files):
    """validate_file_size debe rechazar archivos sobre el límite."""
    with pytest.raises(Exception):
        validate_file_size(tmp_files["big"], 1000)


def test_validate_content_matches_extension_accepts(tmp_files):
    """validate_content_matches_extension debe aceptar coincidencia válida."""
    validate_content_matches_extension(tmp_files["png"])


def test_validate_content_matches_extension_rejects_mismatch(tmp_files):
    """validate_content_matches_extension debe rechazar extensión vs contenido."""
    with pytest.raises(Exception):
        validate_content_matches_extension(tmp_files["mismatch"])


def test_generate_safe_internal_name_strips_traversal():
    """generate_safe_internal_name debe eliminar path traversal."""
    name = generate_safe_internal_name("../../../etc/passwd")
    assert ".." not in name
    assert "/" not in name
    assert name.endswith(".bin")


def test_generate_safe_internal_name_uuid_prefix():
    """generate_safe_internal_name debe empezar con UUID hex."""
    name = generate_safe_internal_name("photo.jpg")
    parts = name.split(".")
    assert len(parts[0]) == 32  # uuid4 hex length
    assert parts[1] in ("jpg", "jpeg", "bin")


def test_validate_dimensions_skips_without_pillow(tmp_files):
    """validate_dimensions no debe fallar si Pillow no está instalado."""
    # Debe retornar sin excepción incluso sin PIL
    validate_dimensions(tmp_files["png"], 4096, 4096)
