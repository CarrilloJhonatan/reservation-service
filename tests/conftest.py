"""Fixtures de testing: DB en memoria + factory helpers."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Reservation, Service, User
from app.enums import ReservationStatus
from app.utils.holidays import is_colombian_holiday

BOG = ZoneInfo("America/Bogota")


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def user_factory(db_session):
    def _make(name="Ana", email=None, is_premium=False):
        email = email or f"{name.lower()}-{id(name)}@test.com"
        u = User(name=name, email=email, is_premium=is_premium)
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        return u
    return _make


@pytest.fixture()
def service_factory(db_session):
    def _make(name="Corte", duration_minutes=60, price=50000, non_refundable=False):
        s = Service(
            name=name,
            duration_minutes=duration_minutes,
            price=price,
            non_refundable=non_refundable,
        )
        db_session.add(s)
        db_session.commit()
        db_session.refresh(s)
        return s
    return _make


@pytest.fixture()
def reservation_factory(db_session):
    def _make(*, user, service, professional_name="Juan",
              start_time: datetime, status=ReservationStatus.ACTIVE):
        r = Reservation(
            user_id=user.id,
            service_id=service.id,
            professional_name=professional_name,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=service.duration_minutes),
            status=status,
            created_at=datetime.now(tz=BOG),
        )
        db_session.add(r)
        db_session.commit()
        db_session.refresh(r)
        return r
    return _make


def next_weekday_at(hour: int, days_ahead: int = 3) -> datetime:
    """Devuelve un datetime aware Bogotá `days_ahead` días en el futuro a la hora dada,
    saltando domingos."""
    base = datetime.now(tz=BOG).replace(hour=hour, minute=0, second=0, microsecond=0)
    target = base + timedelta(days=days_ahead)
    while target.weekday() == 6 or is_colombian_holiday(target.date()):
        target += timedelta(days=1)
    return target
