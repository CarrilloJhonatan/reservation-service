"""Cálculo de reembolsos.

Reglas:
  - Servicio non_refundable → 0
  - Usuario estándar:
      > 24h antes  → 100%
      24h–4h       → 50%
      < 4h         → 0%
  - Usuario premium:
      > 4h antes   → 100%
      4h–1h        → 50%
      < 1h         → 0%
"""
from datetime import datetime, timedelta

from app.models import Reservation


def _percentage(reservation: Reservation, now: datetime) -> float:
    delta: timedelta = reservation.start_time - now
    is_premium = bool(reservation.user.is_premium)

    if is_premium:
        if delta >= timedelta(hours=4):
            return 1.0
        if delta >= timedelta(hours=1):
            return 0.5
        return 0.0

    if delta >= timedelta(hours=24):
        return 1.0
    if delta >= timedelta(hours=4):
        return 0.5
    return 0.0


def calculate_refund(reservation: Reservation, now: datetime) -> float:
    """Monto de reembolso (no porcentaje). 0 si non_refundable."""
    if reservation.service.non_refundable:
        return 0.0
    pct = _percentage(reservation, now)
    return round(float(reservation.service.price) * pct, 2)
