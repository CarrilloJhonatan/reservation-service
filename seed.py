"""Carga `data/seed.json` saneando datos inconsistentes.

Uso (PowerShell):
    python seed.py

Sanitización aplicada (intencional para la prueba):
  - Users:   trim de nombres + lowercase de email + validación Pydantic.
  - Services: validación Pydantic (rechaza precio/duración inválidos).
  - Reservations:
      * Resuelve referencias por email / service_name.
      * Parsea start_time SOLO como ISO 8601 con timezone (rechaza naive
        y formatos no estándar como DD/MM/YYYY).
      * Aplica las reglas de negocio reales vía BookingService:
        domingo, festivos, anticipación, solapamiento, etc.
      * Reporta cada registro omitido con la razón.
"""
import json
import re
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.database import SessionLocal, init_db
from app.exceptions import DomainError
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.reservation import ReservationCreate
from app.schemas.service import ServiceCreate
from app.schemas.user import UserCreate
from app.services.booking_service import BookingService
from sqlalchemy import select

from app.models import Service, User

SEED_PATH = Path("data/seed.json")


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip())


def _parse_start_time(raw: object) -> datetime:
    """Acepta SOLO ISO 8601 con offset/timezone. Rechaza naive y otros formatos."""
    if not isinstance(raw, str):
        raise ValueError("start_time debe ser string ISO 8601")
    # datetime.fromisoformat acepta "2026-06-15T10:00:00-05:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        raise ValueError("start_time debe incluir timezone (offset ISO 8601)")
    return dt


def main() -> None:
    init_db()
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    skipped: list[str] = []
    created = {"users": 0, "services": 0, "reservations": 0}

    with SessionLocal() as db:
        users_repo = UserRepository(db)
        services_repo = ServiceRepository(db)

        # ---- Users ---------------------------------------------------------
        for raw in data.get("users", []):
            try:
                payload = UserCreate(
                    name=_clean_name(raw.get("name", "")),
                    email=(raw.get("email") or "").strip().lower(),
                    is_premium=bool(raw.get("is_premium", False)),
                )
            except ValidationError as e:
                skipped.append(f"user {raw!r}: {e.errors()[0]['msg']}")
                continue
            if users_repo.get_by_email(payload.email):
                continue
            users_repo.create(
                name=payload.name, email=payload.email, is_premium=payload.is_premium
            )
            created["users"] += 1

        # ---- Services ------------------------------------------------------
        for raw in data.get("services", []):
            try:
                payload = ServiceCreate(**raw)
            except ValidationError as e:
                skipped.append(f"service {raw!r}: {e.errors()[0]['msg']}")
                continue
            services_repo.create(
                name=payload.name.strip(),
                duration_minutes=payload.duration_minutes,
                price=payload.price,
                non_refundable=payload.non_refundable,
            )
            created["services"] += 1

        db.commit()

        # ---- Reservations --------------------------------------------------
        booking = BookingService(db)
        for raw in data.get("reservations", []):
            # Resolver referencias por email/nombre — más legible que IDs.
            user = db.execute(
                select(User).where(User.email == (raw.get("user_email") or "").lower())
            ).scalar_one_or_none()
            service = db.execute(
                select(Service).where(Service.name == raw.get("service_name"))
            ).scalar_one_or_none()

            if user is None or service is None:
                skipped.append(
                    f"reservation {raw!r}: usuario o servicio no encontrado"
                )
                continue

            try:
                start = _parse_start_time(raw.get("start_time"))
                payload = ReservationCreate(
                    user_id=user.id,
                    service_id=service.id,
                    professional_name=raw.get("professional_name", ""),
                    start_time=start,
                )
            except (ValueError, ValidationError) as e:
                msg = e.errors()[0]["msg"] if isinstance(e, ValidationError) else str(e)
                skipped.append(f"reservation {raw.get('_comment', raw)!r}: {msg}")
                continue

            try:
                booking.create_reservation(payload)
                created["reservations"] += 1
            except DomainError as e:
                skipped.append(
                    f"reservation {raw.get('_comment', raw)!r}: {e.message}"
                )

    print("Seed completado:")
    for k, v in created.items():
        print(f"  {k:14s} creados: {v}")
    if skipped:
        print(f"\nRegistros omitidos ({len(skipped)}):")
        for s in skipped:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
