"""Configuración de SQLAlchemy.

Nota: Se usa SQLite por simplicidad de la prueba. La capa de repositorios
no contiene dialecto-específicos, lo que facilita migrar a PostgreSQL
cambiando únicamente DATABASE_URL y el driver.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

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
