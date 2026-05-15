"""Tests de reglas de horario: domingo, festivo, anticipación, franja."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.exceptions import InvalidBookingTimeError
from app.services.validation_service import validate_booking_time

BOG = ZoneInfo("America/Bogota")


def _monday_at(hour: int, minute: int = 0) -> datetime:
    """Lunes 4 mayo 2026 (laboral, no festivo) a la hora dada."""
    return datetime(2026, 5, 4, hour, minute, tzinfo=BOG)


def test_rechaza_domingo():
    now = datetime(2026, 5, 1, 8, 0, tzinfo=BOG)
    sunday = datetime(2026, 5, 3, 10, 0, tzinfo=BOG)
    with pytest.raises(InvalidBookingTimeError, match="domingo"):
        validate_booking_time(sunday, 60, now)


def test_rechaza_festivo_colombia_2026():
    # 20 de julio 2026 - lunes festivo
    now = datetime(2026, 7, 18, 8, 0, tzinfo=BOG)
    holiday = datetime(2026, 7, 20, 10, 0, tzinfo=BOG)
    with pytest.raises(InvalidBookingTimeError, match="festivo"):
        validate_booking_time(holiday, 60, now)


def test_rechaza_anticipacion_menor_a_2h():
    now = _monday_at(8, 0)
    start = now + timedelta(hours=1, minutes=59)
    with pytest.raises(InvalidBookingTimeError, match="anticipación"):
        validate_booking_time(start, 30, now)


def test_acepta_anticipacion_exacta_2h():
    now = _monday_at(8, 0)
    start = now + timedelta(hours=2)
    end = validate_booking_time(start, 60, now)
    assert end == start + timedelta(minutes=60)


def test_rechaza_inicio_antes_de_horario():
    now = _monday_at(5, 0)
    start = _monday_at(6, 30)  # antes de 7am
    with pytest.raises(InvalidBookingTimeError):
        validate_booking_time(start, 60, now)


def test_rechaza_fin_despues_de_horario():
    now = _monday_at(5, 0)
    start = _monday_at(18, 30)
    # 18:30 + 60min = 19:30 → fuera
    with pytest.raises(InvalidBookingTimeError, match="finalizar"):
        validate_booking_time(start, 60, now)


def test_acepta_fin_exacto_19h():
    now = _monday_at(5, 0)
    start = _monday_at(18, 0)
    end = validate_booking_time(start, 60, now)
    assert end.hour == 19 and end.minute == 0


def test_rechaza_naive_datetime():
    naive = datetime(2026, 5, 4, 10, 0)
    now = _monday_at(5, 0)
    with pytest.raises(ValueError):
        validate_booking_time(naive, 60, now)
