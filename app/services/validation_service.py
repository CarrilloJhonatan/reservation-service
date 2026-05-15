"""Validación de reglas de horario y festivos.

Funciones puras y testeables: no tocan la base de datos.
"""
from datetime import datetime, timedelta

from app.config import (
    BUSINESS_HOUR_END,
    BUSINESS_HOUR_START,
    MIN_ADVANCE_HOURS,
)
from app.exceptions import InvalidBookingTimeError
from app.utils.datetime_utils import ensure_aware_bogota
from app.utils.holidays import is_colombian_holiday


def validate_booking_time(start: datetime, duration_minutes: int, now: datetime) -> datetime:
    """Valida horario y devuelve `end_time` (Bogotá, aware).

    Reglas:
      - no domingos
      - no festivos Colombia 2026
      - inicio y fin dentro de 07:00–19:00
      - mínimo 2h de anticipación respecto a `now`
    """
    start_bog = ensure_aware_bogota(start)
    now_bog = ensure_aware_bogota(now)

    if start_bog <= now_bog:
        raise InvalidBookingTimeError("La fecha de inicio debe estar en el futuro.")

    if (start_bog - now_bog) < timedelta(hours=MIN_ADVANCE_HOURS):
        raise InvalidBookingTimeError(
            f"Se requiere mínimo {MIN_ADVANCE_HOURS} horas de anticipación."
        )

    # weekday(): lunes=0 ... domingo=6
    if start_bog.weekday() == 6:
        raise InvalidBookingTimeError("No se permiten reservas en domingo.")

    if is_colombian_holiday(start_bog.date()):
        raise InvalidBookingTimeError("No se permiten reservas en festivos.")

    end_bog = start_bog + timedelta(minutes=duration_minutes)

    # Inicio y fin deben caer dentro de la franja horaria.
    if start_bog.hour < BUSINESS_HOUR_START:
        raise InvalidBookingTimeError(
            f"El horario inicia a las {BUSINESS_HOUR_START}:00."
        )
    # `end_bog` puede caer exactamente a las 19:00 (hora de cierre = límite superior).
    end_limit = start_bog.replace(hour=BUSINESS_HOUR_END, minute=0, second=0, microsecond=0)
    if end_bog > end_limit:
        raise InvalidBookingTimeError(
            f"La reserva debe finalizar a más tardar a las {BUSINESS_HOUR_END}:00."
        )

    # Evitar reservas que crucen días (defensivo: con end_limit ya no debería ocurrir).
    if end_bog.date() != start_bog.date():
        raise InvalidBookingTimeError("La reserva no puede cruzar de día.")

    return end_bog
