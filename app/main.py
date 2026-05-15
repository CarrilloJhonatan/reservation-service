"""Punto de entrada de la API."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import APP_NAME, APP_VERSION
from app.database import init_db
from app.exceptions import DomainError
from app.logging_config import setup_logging
from app.routers import reservations, services, users

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "API de gestión de reservas con reglas de negocio reales: horario hábil, "
        "festivos Colombia 2026, límites de cancelación, premium y solapamientos."
    ),
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("App iniciada: %s v%s", APP_NAME, APP_VERSION)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message},
    )


@app.get("/health", tags=["health"], summary="Healthcheck")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(services.router)
app.include_router(reservations.router)
