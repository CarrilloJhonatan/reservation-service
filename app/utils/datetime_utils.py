"""Helpers de fecha/hora timezone-aware (America/Bogota)."""
from datetime import datetime

from app.config import TIMEZONE


def now_bogota() -> datetime:
    """Hora actual en zona Bogotá (aware)."""
    return datetime.now(tz=TIMEZONE)


def ensure_aware_bogota(dt: datetime) -> datetime:
    """Garantiza que el datetime sea aware y esté en Bogotá.

    Si llega naive lanza ValueError (no asumimos timezone implícita).
    Si llega aware en otra timezone lo convertimos a Bogotá.
    """
    if dt.tzinfo is None:
        raise ValueError("datetime debe ser timezone-aware")
    return dt.astimezone(TIMEZONE)
