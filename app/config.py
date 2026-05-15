"""Configuración central de la aplicación."""
from zoneinfo import ZoneInfo

APP_NAME = "Reservation Service"
APP_VERSION = "1.0.0"

DATABASE_URL = "sqlite:///./reservations.db"

TIMEZONE = ZoneInfo("America/Bogota")

# Reglas de negocio
BUSINESS_HOUR_START = 7   # 7:00 AM
BUSINESS_HOUR_END = 19    # 7:00 PM
MIN_ADVANCE_HOURS = 2
MAX_ACTIVE_RESERVATIONS_PER_USER = 3

LOG_DIR = "logs"
LOG_FILE = "logs/app.log"
