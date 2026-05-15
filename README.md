# Reservation Service

![tests](https://github.com/CarrilloJhonatan/reservation-service/actions/workflows/tests.yml/badge.svg)

API de gestión de reservas desarrollada con **FastAPI + SQLite + SQLAlchemy**.
Implementa reglas de negocio reales: horario hábil Bogotá, festivos Colombia 2026,
solapamiento de profesionales, límites de cancelación con políticas estándar/premium
y servicios no reembolsables.

---

## Contexto profesional

La prueba permitía stack libre. Elegí **Python + FastAPI + SQLAlchemy** porque
es exactamente el mismo patrón que vengo aplicando en producción:

- **EvolveAPI (EvolvePos, 2024–2026)**: construí una API en Python/FastAPI que
  integra WordPress, WooCommerce y Uber Direct con el software interno de la
  empresa. Sincroniza productos en tiempo real entre 10+ tiendas, automatiza
  150+ transacciones diarias y soporta hasta 500 órdenes concurrentes.
- Mi día a día principal es **WordPress / WooCommerce / PHP** (40+ sitios,
  plugins propios como [`woo-tax-control`](https://github.com/CarrilloJhonatan/woo-tax-control)
  y `Uber-Direct-Plugin`). Aplico la misma arquitectura en capas (lógica
  centralizada en services, validación en frontera, ORM o `$wpdb` con prepared
  statements en repositorios) tanto en Python como en plugins de WordPress.

Esto deja en evidencia el criterio detrás de las decisiones que verás abajo:
no son patrones académicos, son las mismas decisiones que tomo cuando integro
APIs externas con WooCommerce en producción.

---

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- SQLite
- Pydantic v2
- pytest

---

## Instalación (Windows / PowerShell)

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt
```

Si PowerShell bloquea el script de activación, ejecutar una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## Ejecutar el servidor

```powershell
uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc:      <http://127.0.0.1:8000/redoc>
- OpenAPI:    <http://127.0.0.1:8000/openapi.json>

La base de datos `reservations.db` se crea automáticamente al iniciar.

---

## Cargar datos semilla

```powershell
python seed.py
```

`data/seed.json` contiene **datos inconsistentes intencionales** (emails inválidos,
precios negativos, nombres con espacios sobrantes). El script aplica sanitización
básica y descarta los registros inválidos reportándolos por consola.

---

## Tests

```powershell
pytest
```

Los tests cubren los **edge cases reales**:

- domingos y festivos Colombia 2026
- límite exacto de 2h de anticipación
- inicio y fin dentro de 07:00–19:00
- solapamiento del mismo profesional vs. profesionales distintos
- límite de 3 reservas activas por usuario
- cálculo de reembolso en cada franja (estándar y premium)
- `non_refundable` siempre 0
- límites exactos 24h / 4h / 1h
- rechazo de datetimes naive (timezone obligatoria)

---

## Estructura

```
reservation-service/
├── app/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── config.py            # Configuración (timezone, horarios, límites)
│   ├── database.py          # SQLAlchemy engine y session
│   ├── enums.py             # ReservationStatus
│   ├── exceptions.py        # Excepciones de dominio
│   ├── logging_config.py    # Logging consola + archivo
│   ├── models/              # Entidades ORM
│   ├── schemas/             # Pydantic (validación / serialización)
│   ├── repositories/        # Acceso a datos puro
│   ├── services/            # Lógica de negocio
│   ├── routers/             # HTTP / FastAPI routes
│   └── utils/               # Helpers (fechas, festivos)
├── tests/                   # pytest
├── data/
│   ├── seed.json
│   └── requests.http        # Ejemplos de requests
├── logs/                    # Generado en runtime
├── seed.py                  # Carga seed con sanitización
├── requirements.txt
├── README.md
├── DOC.md
├── NOTAS.md
└── CLAUDE.md
```

---

## Decisiones técnicas

| Decisión | Razón |
|---|---|
| **Capas separadas (router → service → repository → model)** | Separación de responsabilidades clara; cada capa tiene una sola razón para cambiar. |
| **`zoneinfo` + `America/Bogota`** | Forzamos datetimes aware; rechazamos naive en la API y en utilidades. |
| **Festivos hardcoded** | Para 2026 es explícito y revisable. En producción usaría el paquete `holidays` o una tabla de configuración. |
| **`StrEnum` para `ReservationStatus`** | Persiste como string en SQLite y se serializa nativamente. Evita strings mágicos. |
| **Pydantic v2 con `from_attributes`** | Mapeo limpio ORM → schema. |
| **Exception handlers globales** | Errores de dominio se traducen a respuestas JSON consistentes con `status_code` correcto. |
| **`RotatingFileHandler`** | Logs en `logs/app.log` con rotación, sin librerías externas. |
| **Validación de solapamiento en service + índice compuesto en repo** | Lógica defendible; eficiente para volúmenes razonables. |

---

## Trade-offs y limitaciones

- **Concurrencia.** SQLite no soporta `SELECT ... FOR UPDATE`. Para cerrar la
  ventana de carrera entre check de solapamiento e insert dentro de un proceso,
  `BookingService` usa un `threading.Lock` por `professional_name`. Esto es
  defendible para uvicorn con un solo worker. Para múltiples workers o procesos
  la solución correcta es PostgreSQL con constraint `EXCLUDE` sobre `tstzrange`
  (ver sección de migración).
- **Festivos hardcoded** son válidos solo para 2026.
- **Sin autenticación / autorización.** Fuera del alcance de la prueba.
- **Sin cache.** No es necesario al volumen actual.
- **Reservas no se "completan" automáticamente** (estado COMPLETED queda como
  extensibilidad futura; las queries usan `start_time` para filtrar pasadas).

---

## Migración a PostgreSQL

El proyecto está preparado para migrar sin tocar la capa de dominio:

1. Cambiar `DATABASE_URL` en `app/config.py`:
   ```python
   DATABASE_URL = "postgresql+psycopg://user:pass@host:5432/reservations"
   ```
2. Instalar driver: `pip install psycopg[binary]`.
3. Eliminar `connect_args={"check_same_thread": False}` en `database.py`
   (es específico de SQLite).
4. Para concurrencia estricta de reservas, dos opciones:
   - **`SELECT ... FOR UPDATE`** sobre las reservas del profesional dentro de una
     transacción `SERIALIZABLE` o `REPEATABLE READ`.
   - **Constraint `EXCLUDE`** con `btree_gist` y `tstzrange`, por ejemplo:
     ```sql
     ALTER TABLE reservations ADD CONSTRAINT no_overlap
       EXCLUDE USING gist (
         professional_name WITH =,
         tstzrange(start_time, end_time) WITH &&
       ) WHERE (status = 'ACTIVE');
     ```
5. Usar Alembic para migraciones versionadas (en SQLite usamos `create_all`).

---

## Mejoras futuras

- Migraciones con Alembic.
- Autenticación JWT y roles (cliente, profesional, admin).
- Endpoint para horarios disponibles por profesional.
- Notificaciones (email/SMS) en creación y cancelación.
- Tabla de festivos configurable + cálculo automático de Lunes Festivo.
- Job programado que marca reservas pasadas como `COMPLETED`.
- Métricas con Prometheus y tracing OpenTelemetry.

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST   | `/users`                          | Crear usuario |
| GET    | `/users`                          | Listar usuarios |
| POST   | `/services`                       | Crear servicio |
| GET    | `/services`                       | Listar servicios |
| POST   | `/reservations`                   | Crear reserva |
| POST   | `/reservations/{id}/cancel`       | Cancelar y calcular reembolso |
| GET    | `/reservations?user_id&start&end` | Listar por usuario y rango |
| GET    | `/health`                         | Healthcheck |

Ver `data/requests.http` para ejemplos listos para ejecutar desde la extensión
*REST Client* de VS Code.
