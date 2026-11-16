"""Servicio de almacenamiento local de archivos y artefactos.

Proporciona operaciones seguras e idempotentes sobre el filesystem local:
guardar, leer, eliminar, existencia, ruta y hash SHA-256. Los nombres de
archivo se generan internamente (never use client-provided names directly)
para prevenir path traversal y sobrescrituras accidentales.

Todos los binarios se almacenan en disco; PostgreSQL conserva solo
metadatos y referencias (artifact_id).
"""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class StorageService:
    """Operaciones de almacenamiento local de archivos.

    Expone métodos para guardar, leer, eliminar y consultar artefactos
    bajo un directorio raíz configurable (``STORAGE_ROOT``).
    """

    def __init__(self, storage_root: str | None = None) -> None:
        settings = get_settings()
        self.root = Path(storage_root or settings.STORAGE_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def _artifact_dir(self, artifact_type: str) -> Path:
        """Devuelve el directorio para un tipo de artefacto, creándolo si falta."""
        directory = self.root / artifact_type
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def _safe_extension(original_name: str | None) -> str:
        """Extrae una extensión segura a partir del nombre original.

        Retorna solo la extensión (con punto), nunca el nombre del cliente,
        para prevenir path traversal y sobrescrituras accidentales.
        """
        if not original_name:
            return ""
        suffix = Path(original_name).suffix.lower()
        dangerous = {".exe", ".bat", ".sh", ".ps1", ".dll", ".so"}
        if suffix in dangerous or len(suffix) > 10:
            return ".bin"
        return suffix

    @staticmethod
    def sha256_of_file(path: str | Path) -> str:
        """Calcula el hash SHA-256 de un archivo existente."""
        hash_sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def save(
        self,
        source_path: str | Path,
        artifact_type: str,
        original_name: str | None = None,
    ) -> dict[str, Any]:
        """Guarda un archivo bajo ``<root>/<artifact_type>/`` con nombre seguro.

        Retorna un diccionario con metadatos del artefacto:
        ``artifact_id``, ``tipo``, ``ruta_archivo``, ``hash_sha256``,
        ``tamano_bytes``, ``nombre_original``.

        La operación es idempotente en el sentido de que cada llamada
        genera un artifact_id nuevo; no sobrescribe archivos existentes.
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        target_dir = self._artifact_dir(artifact_type)
        artifact_id = uuid.uuid4()
        ext = self._safe_extension(original_name or source.name)
        target_path = target_dir / f"{artifact_id}{ext}"

        shutil.copy2(source, target_path)

        file_hash = self.sha256_of_file(target_path)
        size_bytes = target_path.stat().st_size

        return {
            "artifact_id": str(artifact_id),
            "tipo": artifact_type,
            "ruta_archivo": str(target_path),
            "hash_sha256": file_hash,
            "tamano_bytes": size_bytes,
            "nombre_original": original_name or source.name,
        }

    def read(self, artifact_id: str, artifact_type: str) -> bytes:
        """Lee el contenido binario de un artefacto por su ID y tipo."""
        target_dir = self._artifact_dir(artifact_type)
        # Buscar el archivo que comience con el artifact_id
        for candidate in target_dir.iterdir():
            if candidate.stem == artifact_id:
                return candidate.read_bytes()
        raise FileNotFoundError(f"Artifact not found: {artifact_id} (type={artifact_type})")

    def exists(self, artifact_id: str, artifact_type: str) -> bool:
        """Retorna True si existe un artefacto con el ID y tipo dados."""
        target_dir = self._artifact_dir(artifact_type)
        return any(candidate.stem == artifact_id for candidate in target_dir.iterdir())

    def path(self, artifact_id: str, artifact_type: str) -> Path:
        """Devuelve la ruta del filesystem de un artefacto sin leerlo."""
        target_dir = self._artifact_dir(artifact_type)
        for candidate in target_dir.iterdir():
            if candidate.stem == artifact_id:
                return candidate
        raise FileNotFoundError(f"Artifact not found: {artifact_id} (type={artifact_type})")

    def delete(self, artifact_id: str, artifact_type: str) -> bool:
        """Elimina un artefacto por ID y tipo. Retorna False si no existía."""
        target_dir = self._artifact_dir(artifact_type)
        for candidate in target_dir.iterdir():
            if candidate.stem == artifact_id:
                candidate.unlink()
                return True
        return False

    def list_by_type(self, artifact_type: str) -> list[dict[str, Any]]:
        """Lista todos los artefactos de un tipo dado."""
        target_dir = self._artifact_dir(artifact_type)
        results: list[dict[str, Any]] = []
        for candidate in target_dir.iterdir():
            if candidate.is_file():
                results.append(
                    {
                        "artifact_id": candidate.stem,
                        "tipo": artifact_type,
                        "ruta_archivo": str(candidate),
                        "tamano_bytes": candidate.stat().st_size,
                    }
                )
        return results
