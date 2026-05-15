"""Carga `data/seed.json` saneando datos inconsistentes.

Uso (PowerShell):
    python seed.py

Sanitización aplicada (intencional para la prueba):
  - Trim de nombres + colapso de espacios.
  - Lowercase de emails.
  - Validación con Pydantic: registros inválidos se reportan y omiten.
"""
import json
import re
from pathlib import Path

from pydantic import ValidationError

from app.database import SessionLocal, init_db
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.service import ServiceCreate
from app.schemas.user import UserCreate

SEED_PATH = Path("data/seed.json")


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip())


def main() -> None:
    init_db()
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    skipped: list[str] = []

    with SessionLocal() as db:
        users_repo = UserRepository(db)
        services_repo = ServiceRepository(db)

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

        db.commit()

    print(f"Seed completado. Usuarios y servicios cargados desde {SEED_PATH}.")
    if skipped:
        print("Registros omitidos por validación:")
        for s in skipped:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
