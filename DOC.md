# DOC.md — Guía técnica del proyecto

Este documento describe **cómo trabajar dentro del proyecto** de forma
consistente. Está pensado para que cualquier desarrollador (o asistente IA)
pueda extender el código manteniendo el estilo.

---

## 1. Contexto

Sistema de gestión de reservas. Reglas de negocio reales (horario hábil
Bogotá, festivos, reembolsos, premium, solapamientos).

Prioridades:

- claridad
- mantenibilidad
- separación de responsabilidades
- código defendible en entrevista técnica

---

## 2. Arquitectura

Capas, en orden de dependencia (cada capa solo conoce las que están a su
derecha):

```
router  →  service  →  repository  →  model
                      ↑
                   schema (Pydantic)
                   utils (helpers puros)
```

### Responsabilidades

| Capa | Sí | No |
|---|---|---|
| **router** | Recibir HTTP, validar payload con Pydantic, delegar al service, serializar respuesta. | Lógica de negocio, queries, manejar transacciones. |
| **service** | Reglas de negocio, orquestación, commit de transacción. | Acceso directo al ORM, parseo HTTP. |
| **repository** | Queries, inserts, updates con SQLAlchemy. | Reglas de negocio, validaciones. |
| **model** | Definición ORM, índices. | Lógica. |
| **schema** | Validación de entrada, serialización de salida. | Acceso a DB. |
| **utils** | Helpers puros (fechas, festivos). | Estado, dependencias. |

---

## 3. Convenciones

- **Tipado fuerte** en toda la API pública (parámetros y retornos).
- **`from __future__` no se usa**: Python 3.12 ya soporta `X | Y`.
- **Snake_case** para módulos, funciones y variables.
- **PascalCase** para clases.
- **Constantes en `UPPER_SNAKE`** en `config.py`.
- **Strings mágicos prohibidos**: usar enums.
- **Comentarios** solo cuando explican *por qué*, no *qué*.
- **Docstrings cortas** en módulos y funciones no triviales.

### Fechas

- Toda fecha es **timezone-aware** en `America/Bogota`.
- Datetimes naive se **rechazan** (ver `ensure_aware_bogota`).
- Persistimos con `DateTime(timezone=True)`.

---

## 4. Cómo agregar un nuevo endpoint

1. **Schema** en `app/schemas/<recurso>.py`
   (Pydantic, separar `*Create` de `*Out`).
2. **Repository** en `app/repositories/<recurso>_repository.py`
   si requiere queries nuevas.
3. **Service** en `app/services/<recurso>_service.py`
   con la lógica de negocio.
4. **Router** en `app/routers/<recurso>.py` con:
   - `summary` y `description` claros.
   - `response_model` tipado.
   - `responses={...}` documentando códigos de error relevantes.
5. **Registrar** el router en `app/main.py` con `app.include_router(...)`.
6. **Tests** en `tests/test_<recurso>.py` cubriendo edge cases reales.

---

## 5. Cómo escribir un test

- Usar las fixtures de `tests/conftest.py`: `db_session`, `user_factory`,
  `service_factory`, `reservation_factory`.
- Para fechas usar `next_weekday_at(...)` o construir explícitamente con
  `ZoneInfo("America/Bogota")`.
- Probar **límites exactos** (24h, 4h, 1h, 07:00, 19:00).
- Probar el caso **negativo** además del positivo.
- Evitar tests triviales (no testear getters).

Ejemplo mínimo:

```python
def test_caso(db_session, user_factory, service_factory):
    user = user_factory(is_premium=True)
    service = service_factory(price=100000)
    # ... actuar ...
    # ... asertar comportamiento de negocio ...
```

---

## 6. Errores

Todas las excepciones de dominio extienden `DomainError` y declaran su
`status_code`. El handler global en `main.py` las traduce a:

```json
{ "error": "BookingConflictError", "message": "..." }
```

No lanzar `HTTPException` desde services; eso es responsabilidad del
handler. Los routers tampoco deberían capturar excepciones de dominio.

---

## 7. Logging

- `logging.getLogger(__name__)` por módulo.
- Loggear eventos de negocio relevantes: creación y cancelación.
- No loggear datos sensibles.
- Niveles: `INFO` para eventos normales, `WARNING` para situaciones
  recuperables, `ERROR` para fallos.

---

## 8. Reglas de negocio (resumen)

| Regla | Valor |
|---|---|
| Días permitidos | Lunes a sábado |
| Horario | 07:00 – 19:00 hora Bogotá |
| Festivos | Colombia 2026 (hardcoded en `utils/holidays.py`) |
| Anticipación mínima | 2 horas |
| Máx. reservas activas futuras / usuario | 3 |
| Reembolso estándar | >24h: 100%, 24–4h: 50%, <4h: 0% |
| Reembolso premium | >4h: 100%, 4–1h: 50%, <1h: 0% |
| `non_refundable` | Siempre 0% |

---

## 9. Anti-patrones a evitar

- Lógica de negocio en routers.
- Queries embebidas en services.
- `datetime.now()` sin timezone.
- Strings hardcoded para estados.
- Capturar `Exception` genérica.
- Tests que solo verifican que el código compila.
- Comentarios que repiten el nombre de la función.
