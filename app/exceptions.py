"""Excepciones de dominio.

Los routers traducen estas excepciones a respuestas HTTP coherentes
mediante exception handlers registrados en main.py.
"""


class DomainError(Exception):
    """Excepción base de dominio."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BookingConflictError(DomainError):
    """Solapamiento de reservas para el mismo profesional."""

    status_code = 409


class InvalidBookingTimeError(DomainError):
    """Horario inválido: fuera de horario, domingo, festivo, sin anticipación, etc."""

    status_code = 422


class RefundNotAllowedError(DomainError):
    """Reembolso no permitido (servicio non_refundable, ya cancelada, etc.)."""

    status_code = 409


class ReservationLimitExceededError(DomainError):
    """Usuario excede el máximo de reservas activas futuras."""

    status_code = 409


class NotFoundError(DomainError):
    status_code = 404
