"""Tests de integración del BookingService: solapamientos, límite 3, listado."""
from datetime import timedelta

import pytest

from app.exceptions import (
    BookingConflictError,
    ReservationLimitExceededError,
)
from app.schemas.reservation import ReservationCreate
from app.services.booking_service import BookingService

from .conftest import next_weekday_at


def test_crea_reserva_exitosa(db_session, user_factory, service_factory):
    user = user_factory()
    svc = service_factory(duration_minutes=60)
    start = next_weekday_at(hour=10, days_ahead=3)

    r = BookingService(db_session).create_reservation(
        ReservationCreate(
            user_id=user.id, service_id=svc.id,
            professional_name="Pedro", start_time=start,
        )
    )
    assert r.id is not None
    assert r.end_time == r.start_time + timedelta(minutes=60)


def test_solapamiento_mismo_profesional(db_session, user_factory, service_factory):
    user = user_factory()
    svc = service_factory(duration_minutes=60)
    start = next_weekday_at(hour=10, days_ahead=3)
    svc_obj = BookingService(db_session)

    svc_obj.create_reservation(
        ReservationCreate(user_id=user.id, service_id=svc.id,
                          professional_name="Pedro", start_time=start)
    )
    # Solapa: empieza 30min después.
    with pytest.raises(BookingConflictError):
        svc_obj.create_reservation(
            ReservationCreate(
                user_id=user.id, service_id=svc.id,
                professional_name="Pedro",
                start_time=start + timedelta(minutes=30),
            )
        )


def test_otro_profesional_no_solapa(db_session, user_factory, service_factory):
    user = user_factory()
    svc = service_factory(duration_minutes=60)
    start = next_weekday_at(hour=10, days_ahead=3)
    svc_obj = BookingService(db_session)

    svc_obj.create_reservation(
        ReservationCreate(user_id=user.id, service_id=svc.id,
                          professional_name="Pedro", start_time=start)
    )
    # Otro profesional en el mismo horario → OK.
    r2 = svc_obj.create_reservation(
        ReservationCreate(user_id=user.id, service_id=svc.id,
                          professional_name="Laura", start_time=start)
    )
    assert r2.id is not None


def test_limite_3_reservas_activas(db_session, user_factory, service_factory):
    user = user_factory()
    svc = service_factory(duration_minutes=60)
    bs = BookingService(db_session)

    base = next_weekday_at(hour=8, days_ahead=3)
    for i, prof in enumerate(["P1", "P2", "P3"]):
        bs.create_reservation(
            ReservationCreate(
                user_id=user.id, service_id=svc.id,
                professional_name=prof,
                start_time=base + timedelta(hours=2 * i),
            )
        )

    with pytest.raises(ReservationLimitExceededError):
        bs.create_reservation(
            ReservationCreate(
                user_id=user.id, service_id=svc.id,
                professional_name="P4",
                start_time=base + timedelta(hours=8),
            )
        )
