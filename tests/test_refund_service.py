"""Tests de cálculo de reembolso (estándar, premium, non_refundable)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.refund_service import calculate_refund

BOG = ZoneInfo("America/Bogota")


def _now() -> datetime:
    return datetime(2026, 5, 4, 8, 0, tzinfo=BOG)


def test_non_refundable_siempre_cero(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=False)
    service = service_factory(price=100000, non_refundable=True)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(days=30))
    assert calculate_refund(r, _now()) == 0.0


def test_standard_mas_de_24h_reembolso_completo(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=False)
    service = service_factory(price=100000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=25))
    assert calculate_refund(r, _now()) == 100000.0


def test_standard_entre_4_y_24_reembolsa_50(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=False)
    service = service_factory(price=100000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=10))
    assert calculate_refund(r, _now()) == 50000.0


def test_standard_menos_de_4h_sin_reembolso(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=False)
    service = service_factory(price=100000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=3))
    assert calculate_refund(r, _now()) == 0.0


def test_premium_mas_de_4h_completo(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=True)
    service = service_factory(price=200000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=5))
    assert calculate_refund(r, _now()) == 200000.0


def test_premium_entre_1_y_4h_50(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=True)
    service = service_factory(price=200000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=2))
    assert calculate_refund(r, _now()) == 100000.0


def test_premium_menos_de_1h_cero(reservation_factory, user_factory, service_factory):
    user = user_factory(is_premium=True)
    service = service_factory(price=200000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(minutes=30))
    assert calculate_refund(r, _now()) == 0.0


def test_limite_exacto_24h_standard(reservation_factory, user_factory, service_factory):
    """Exactamente 24h → cuenta como >= 24h → 100%."""
    user = user_factory(is_premium=False)
    service = service_factory(price=100000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=24))
    assert calculate_refund(r, _now()) == 100000.0


def test_limite_exacto_4h_standard(reservation_factory, user_factory, service_factory):
    """Exactamente 4h → cae en franja 50%."""
    user = user_factory(is_premium=False)
    service = service_factory(price=100000)
    r = reservation_factory(user=user, service=service, start_time=_now() + timedelta(hours=4))
    assert calculate_refund(r, _now()) == 50000.0
