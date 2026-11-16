"""Errores base de la aplicación con code, message, details y request_id."""

from typing import Any


class AppError(Exception):
    """Error base de la aplicación."""

    code: str = "app_error"
    message: str = "Ocurrió un error inesperado"
    details: dict[str, Any] | None = None
    request_id: str | None = None

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
        code: str | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or self.details
        self.request_id = request_id
        if code is not None:
            self.code = code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
        }


class NotFoundError(AppError):
    code = "not_found"
    message = "Recurso no encontrado"


class ValidationError(AppError):
    code = "validation_error"
    message = "Error de validación"


class ConflictError(AppError):
    code = "conflict"
    message = "Conflicto de estado"


class UnauthorizedError(AppError):
    code = "unauthorized"
    message = "No autorizado"


class ForbiddenError(AppError):
    code = "forbidden"
    message = "Acceso denegado"


class InternalError(AppError):
    code = "internal_error"
    message = "Error interno del servidor"
