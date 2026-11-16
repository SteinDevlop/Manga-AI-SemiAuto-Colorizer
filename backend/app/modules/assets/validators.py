"""File validators for the assets module.

Provides pure validation functions over local files: MIME type, size,
dimensions, content-vs-extension consistency, and safe internal name
generation. All validation errors use ``ValidationError`` from
``app.core.exceptions`` and follow the envelope ``code/message/details``.

No binary data is stored in PostgreSQL; only local file validation is
performed. Heavy AI inference is never executed here.
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from pathlib import Path
from typing import Final

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

#: Extension -> expected MIME type used by the extension fallback.
_EXTENSION_TO_MIME: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".svg": "image/svg+xml",
}

#: Dangerous extensions that must never be treated as image content.
_DANGEROUS_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".sh",
        ".ps1",
        ".dll",
        ".so",
        ".scr",
        ".vbs",
        ".js",
        ".jar",
    }
)

#: Magic byte signatures mapped to their canonical MIME type.
_MAGIC_BYTES: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # WEBP starts with RIFF....WEBP
    (b"BM", "image/bmp"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
    (b"%PDF", "application/pdf"),
)

#: Dangerous magic byte signatures that must be rejected outright.
_DANGEROUS_MAGIC: tuple[bytes, ...] = (
    b"MZ",  # PE / Windows executable
    b"\x7fELF",  # ELF executable
    b"#!",  # shell script
)


def _is_image_extension(extension: str) -> bool:
    """Return True if ``extension`` looks like a common image extension."""
    return extension.lower() in _EXTENSION_TO_MIME


def _mime_by_extension(file_path: Path) -> str | None:
    """Guess the MIME type from the file extension as a last resort."""
    guessed, _ = mimetypes.guess_type(file_path.name)
    if guessed:
        return guessed
    return _EXTENSION_TO_MIME.get(file_path.suffix.lower())


def _detect_mime_with_libraries(file_path: Path) -> str | None:
    """Try optional third-party libraries to detect the real MIME type."""
    # filetype (magic bytes based, no external ``file`` binary needed).
    try:
        import filetype  # type: ignore[import-not-found]

        kind = filetype.guess(str(file_path))
        if kind is not None:
            return kind.mime
    except Exception:  # pragma: no cover - optional dependency missing
        logger.debug("filetype library unavailable for %s", file_path)

    # imghdr (standard library, image-only, deprecated in 3.11 but present).
    try:
        import imghdr  # type: ignore[deprecated]

        detected = imghdr.what(str(file_path))
        if detected is not None:
            mapping = {
                "png": "image/png",
                "jpeg": "image/jpeg",
                "jpg": "image/jpeg",
                "gif": "image/gif",
                "bmp": "image/bmp",
                "tiff": "image/tiff",
                "webp": "image/webp",
            }
            return mapping.get(detected, f"image/{detected}")
    except Exception:  # pragma: no cover - standard library should exist
        logger.debug("imghdr unavailable for %s", file_path)

    return None


def validate_mime_type(file_path: str | Path, allowed_mimes: set[str]) -> None:
    """Verify that the real MIME type of ``file_path`` is in ``allowed_mimes``.

    Detection order: optional ``filetype`` library, optional ``imghdr``,
    then extension-based guess as a fallback. Raises ``ValidationError``
    when the detected MIME type is not in the allowed set.

    Args:
        file_path: Path to the file to validate.
        allowed_mimes: Set of MIME type strings that are permitted.

    Raises:
        ValidationError: If the file does not exist or its MIME type is not
            allowed.
    """
    path = Path(file_path)
    if not path.is_file():
        raise ValidationError(
            message=f"File not found: {path}",
            details={"path": str(path), "code": "file_not_found"},
        )

    detected = _detect_mime_with_libraries(path)
    if detected is None:
        detected = _mime_by_extension(path) or "application/octet-stream"

    if detected not in allowed_mimes:
        raise ValidationError(
            message=(
                f"MIME type not allowed: {detected} (expected one of {sorted(allowed_mimes)})"
            ),
            details={
                "path": str(path),
                "detected_mime": detected,
                "allowed_mimes": sorted(allowed_mimes),
                "code": "mime_type_not_allowed",
            },
        )


def validate_file_size(file_path: str | Path, max_size_bytes: int) -> None:
    """Verify that the file size does not exceed ``max_size_bytes``.

    Args:
        file_path: Path to the file to validate.
        max_size_bytes: Maximum allowed size in bytes (inclusive).

    Raises:
        ValidationError: If the file does not exist or its size exceeds the
            limit.
    """
    path = Path(file_path)
    if not path.is_file():
        raise ValidationError(
            message=f"File not found: {path}",
            details={"path": str(path), "code": "file_not_found"},
        )

    size_bytes = path.stat().st_size
    if size_bytes > max_size_bytes:
        raise ValidationError(
            message=(f"File size exceeds limit: {size_bytes} bytes (max {max_size_bytes} bytes)"),
            details={
                "path": str(path),
                "size_bytes": size_bytes,
                "max_size_bytes": max_size_bytes,
                "code": "file_size_exceeds_limit",
            },
        )


def validate_dimensions(
    file_path: str | Path,
    max_width: int,
    max_height: int,
) -> None:
    """Verify image dimensions do not exceed ``max_width``/``max_height``.

    Uses Pillow (PIL) when available. If Pillow is not installed, the
    check is skipped with a log warning and no error is raised, per the
    requirement to avoid failing when the image library is missing.

    Args:
        file_path: Path to the image file to validate.
        max_width: Maximum allowed width in pixels.
        max_height: Maximum allowed height in pixels.

    Raises:
        ValidationError: If the file does not exist, is not a readable
            image, or its dimensions exceed the limits.
    """
    path = Path(file_path)
    if not path.is_file():
        raise ValidationError(
            message=f"File not found: {path}",
            details={"path": str(path), "code": "file_not_found"},
        )

    try:
        from PIL import Image  # type: ignore[import-not-found]
    except Exception:  # pragma: no cover - optional dependency missing
        logger.warning(
            "Pillow (PIL) not installed; skipping dimension check for %s",
            path,
        )
        return

    try:
        with Image.open(path) as image:
            width, height = image.size
    except Exception as exc:  # pragma: no cover - unreadable image
        raise ValidationError(
            message=f"Unable to read image dimensions: {path}",
            details={
                "path": str(path),
                "error": str(exc),
                "code": "unreadable_image",
            },
        ) from exc

    if width > max_width or height > max_height:
        raise ValidationError(
            message=(
                f"Image dimensions exceed limits: {width}x{height} (max {max_width}x{max_height})"
            ),
            details={
                "path": str(path),
                "width": width,
                "height": height,
                "max_width": max_width,
                "max_height": max_height,
                "code": "dimensions_exceed_limits",
            },
        )


def _mime_for_extension(extension: str) -> str | None:
    """Return the expected MIME type for ``extension`` (lowercased, with dot)."""
    ext = extension.lower()
    if ext in _EXTENSION_TO_MIME:
        return _EXTENSION_TO_MIME[ext]
    guessed, _ = mimetypes.guess_type(f"file{ext}")
    return guessed


def _detect_mime_by_magic_bytes(file_path: Path) -> str | None:
    """Detect MIME type from the file's magic bytes (file header)."""
    try:
        with open(file_path, "rb") as handle:
            header = handle.read(32)
    except OSError:
        return None

    for dangerous in _DANGEROUS_MAGIC:
        if header.startswith(dangerous):
            return f"application/dangerous-{dangerous[:4]!r}"

    for signature, mime in _MAGIC_BYTES:
        if header.startswith(signature):
            # WEBP needs an extra check: RIFF....WEBP
            if mime == "image/webp" and b"WEBP" not in header[8:12]:
                continue
            return mime

    return None


def validate_content_matches_extension(file_path: str | Path) -> None:
    """Verify that the real file content matches its extension.

    Compares magic bytes at the start of the file against the MIME type
    implied by the file extension. Raises ``ValidationError`` on
    discrepancy (e.g. a PHP script renamed to ``.jpg``).

    Args:
        file_path: Path to the file to validate.

    Raises:
        ValidationError: If the file does not exist, has a dangerous type,
            or its content does not match its extension.
    """
    path = Path(file_path)
    if not path.is_file():
        raise ValidationError(
            message=f"File not found: {path}",
            details={"path": str(path), "code": "file_not_found"},
        )

    extension = path.suffix.lower()
    if extension in _DANGEROUS_EXTENSIONS:
        raise ValidationError(
            message=f"Dangerous file extension not allowed: {extension}",
            details={
                "path": str(path),
                "extension": extension,
                "code": "dangerous_extension",
            },
        )

    detected_magic = _detect_mime_by_magic_bytes(path)
    expected_mime = _mime_for_extension(extension)

    # No extension means we cannot verify content vs extension; allow it.
    if not extension:
        return

    # Dangerous content detected regardless of extension.
    if detected_magic is not None and detected_magic.startswith("application/dangerous-"):
        raise ValidationError(
            message=f"Dangerous file content detected: {path}",
            details={
                "path": str(path),
                "detected": detected_magic,
                "code": "dangerous_content",
            },
        )

    # If the extension implies a known type but we could not detect any
    # magic bytes, the content does not match the extension: reject it.
    if expected_mime is not None and detected_magic is None:
        raise ValidationError(
            message=(
                f"Content does not match extension: no recognizable magic "
                f"bytes for {extension} (expected {expected_mime})"
            ),
            details={
                "path": str(path),
                "extension": extension,
                "expected_mime": expected_mime,
                "detected_mime": None,
                "code": "content_extension_mismatch",
            },
        )

    # If we detected magic bytes but they do not match the extension, reject.
    if expected_mime is not None and detected_magic != expected_mime:
        raise ValidationError(
            message=(
                f"Content does not match extension: detected {detected_magic} "
                f"but extension {extension} implies {expected_mime}"
            ),
            details={
                "path": str(path),
                "extension": extension,
                "expected_mime": expected_mime,
                "detected_mime": detected_magic,
                "code": "content_extension_mismatch",
            },
        )


def generate_safe_internal_name(original_name: str) -> str:
    """Generate a safe internal file name from ``original_name``.

    The result is ``<uuid>.<safe_extension>``. The extension is sanitized:
    lowercased, stripped of path separators and dangerous characters, and
    replaced with ``.bin`` when it is dangerous or empty. Path traversal
    sequences (``..``, slashes) are removed so the name can never escape
    its target directory.

    Args:
        original_name: The client-provided original file name.

    Returns:
        A safe internal name such as ``<uuid hex>.png``.
    """
    name = (original_name or "").strip()
    # Remove any directory components and traversal attempts.
    base_name = Path(name).name
    suffix = Path(base_name).suffix.lower()

    dangerous = {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".sh",
        ".ps1",
        ".dll",
        ".so",
        ".scr",
        ".vbs",
        ".js",
        ".jar",
    }
    if suffix in dangerous or not suffix:
        suffix = ".bin"

    # Keep only alphanumerics, dots, dashes and underscores in the stem
    # portion of the extension to avoid dangerous characters.
    safe_suffix = "".join(ch for ch in suffix if ch.isalnum() or ch in {".", "-", "_"})
    if not safe_suffix or safe_suffix == ".":
        safe_suffix = ".bin"

    return f"{uuid.uuid4().hex}{safe_suffix}"


__all__: Final[list[str]] = [
    "validate_mime_type",
    "validate_file_size",
    "validate_dimensions",
    "validate_content_matches_extension",
    "generate_safe_internal_name",
]
