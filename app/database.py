"""Configuración de SQLAlchemy.

Nota: Se usa SQLite por simplicidad de la prueba. La capa de repositorios
no contiene dialecto-específicos, lo que facilita migrar a PostgreSQL
cambiando únicamente DATABASE_URL y el driver.
"""
from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import DateTime, TypeDecorator, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


class UTCDateTime(TypeDecorator):
    """DateTime que SIEMPRE almacena en UTC y devuelve aware.

    SQLite no preserva tzinfo aunque la columna sea DateTime(timezone=True).
    En PostgreSQL `timestamptz` lo hace nativamente; esta capa garantiza el
    mismo comportamiento en ambos motores.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Solo se persisten datetimes timezone-aware")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

# check_same_thread=False es necesario para FastAPI con SQLite.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Importar modelos para registrarlos en el metadata.
    from app.models import reservation, service, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
