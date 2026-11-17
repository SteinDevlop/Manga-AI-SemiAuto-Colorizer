"""Configuración de logging estructurado para el backend SUMI.

Proporciona un logger con formato JSON consistente para facilitar el
rastreo de errores y el monitoreo en producción. Todos los módulos deben
obtener su logger mediante get_logger(__name__).
"""
from __future__ import annotations

import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Formateador JSON estructurado para logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return str(log_record)


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado con formato estructurado."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
