# NOTAS.md — Uso de IA durante el desarrollo

Este documento es transparente sobre el uso de **Claude (Sonnet/Opus en Claude
Code)** como herramienta de productividad durante la implementación de la
prueba técnica.

---

## Qué partes fueron generadas con IA

Claude generó el **primer borrador** de:

- Layout del proyecto y boilerplate (SQLAlchemy 2.x con `Mapped`,
  Pydantic v2 schemas, routers FastAPI).
- Implementación inicial de `validation_service`, `refund_service` y
  `booking_service`.
- Repositorios y modelos ORM.
- Suite de tests con pytest (fixtures + casos de borde).
- Redacción de README, DOC.md y este archivo.

---

## Qué fue ajustado o reescrito manualmente

Las correcciones nacieron de **probar el código** y revisar contra el
enunciado, no de aceptar el primer output:

### 1. Bug timezone con SQLite (encontrado al correr los tests)

El primer borrador usaba `DateTime(timezone=True)` directamente en las
columnas. Al correr la suite de tests, **12 de 21 tests fallaron** con
`TypeError: can't subtract offset-naive and offset-aware datetimes`.

Causa: SQLite **no preserva `tzinfo`** aunque la columna se declare con
`timezone=True` — eso solo lo hace PostgreSQL (`timestamptz`).

Solución: añadí un `TypeDecorator` (`UTCDateTime` en `app/database.py`)
que persiste siempre en UTC y devuelve datetimes aware al leer.
Esto deja el código **idéntico al comportamiento de PostgreSQL** y
sobrevive a la migración sin cambios.

### 2. Concurrencia básica

La IA solo había dejado un comentario *"limitación de SQLite"*. Lo elevé
a una implementación real: `threading.Lock` por `professional_name` en
`BookingService` que serializa el check-then-insert dentro del proceso.
Defendible para uvicorn con un solo worker; documentado en el README
que la solución a escala es el constraint `EXCLUDE` de PostgreSQL con
`tstzrange`.

### 3. Reembolsos — validación de límites exactos

Revisé manualmente la matriz (estándar y premium) y confirmé que cada
franja usa el comparador correcto:

| Franja | Comparador |
|---|---|
| Estándar >24h | `>= timedelta(hours=24)` |
| Estándar 24–4h | `>= timedelta(hours=4)` |
| Premium >4h | `>= timedelta(hours=4)` |
| Premium 4–1h | `>= timedelta(hours=1)` |

Agregué tests específicos para los límites exactos (24h, 4h, 1h) porque
es el bug clásico de "off-by-one".

### 4. Festivos Colombia 2026

Verifiqué manualmente la lista de 18 festivos contra el calendario
oficial (Ley 51 de 1983) y los traslados al lunes. Esto importó: durante
la verificación del seed descubrí que **2026-06-15 es Sagrado Corazón
trasladado**, no un lunes laboral, y corregí las fechas de las reservas
válidas del seed.

### 5. Timezone obligatoria en la API

Forcé que la API rechace datetimes naive en dos puntos:
1. En el `field_validator` de `ReservationCreate` (frontera HTTP).
2. En `ensure_aware_bogota` y en `UTCDateTime.process_bind_param`
   (frontera DB).

Defensa en profundidad para evitar el bug clásico de "8am UTC vs 8am
Bogotá".

### 6. Manejo de errores

Extendí la jerarquía de excepciones para no abusar de los códigos 400/422:

- `BookingConflictError` → 409
- `InvalidBookingTimeError` → 422
- `RefundNotAllowedError` → 409
- `ReservationLimitExceededError` → 409
- `NotFoundError` → 404

Y un único exception handler global en `main.py` que traduce a JSON
consistente.

### 7. Seed con inconsistencias

El primer borrador solo tenía inconsistencias en users/services. El
enunciado pide explícitamente *"fechas en distintos formatos, campos
faltantes"*, así que añadí un bloque `reservations` con 9 casos:

- 2 válidas (lunes/martes laborales)
- 1 que genera conflicto de solapamiento con la primera
- 6 inválidas: formato DD/MM/YYYY, naive, fecha pasada, campo faltante,
  domingo, festivo

El `seed.py` parsea, sanitiza, intenta crearlas vía `BookingService` y
**reporta cada omisión con la razón exacta** (en consola). Es la
materialización del criterio *"decide cómo manejarlas"*.

### 8. Limpieza de código muerto

Quité `ReservationStatus.COMPLETED` del enum porque nunca se usaba;
el flujo del negocio solo necesita `ACTIVE` / `CANCELLED`. CLAUDE.md
explícitamente pide evitar enums hardcodeados pero también código no
utilizado.

---

## Decisiones de diseño tomadas

| Decisión | Justificación |
|---|---|
| Capas explícitas (router/service/repository) sin Unit of Work ni DTOs separados | La prueba pide claridad y separación, no DDD. |
| `StrEnum` para `ReservationStatus` | Serialización JSON nativa y persistencia limpia. |
| `init_db()` con `create_all` en lugar de Alembic | Para una prueba técnica Alembic suma complejidad sin valor. Documentado como mejora futura. |
| Exception handler global vs. try/except en routers | DRY y consistencia. |
| Sin autenticación | El enunciado lo prohíbe explícitamente ("autenticación compleja: NO"). |
| Logging con `RotatingFileHandler` de stdlib | Sin dependencias externas tipo `loguru`. |
| `UTCDateTime` TypeDecorator | Hace la capa de persistencia portable entre SQLite y PostgreSQL. |
| Lock en proceso por profesional | Más granular que un lock global; defendible para 1 worker. |

---

## Casos concretos donde rechacé sugerencias de Claude

La IA no es infalible. Estos son ejemplos reales de este mismo proyecto donde
ignoré o reescribí la propuesta inicial:

1. **`DateTime(timezone=True)` en SQLite.** El primer borrador asumía que
   declarar la columna con `timezone=True` bastaba. Al correr los tests, 12
   fallaron. **Diagnostiqué la causa real** (SQLite no preserva tzinfo, solo
   PostgreSQL con `timestamptz` lo hace) y diseñé un `TypeDecorator`
   (`UTCDateTime`) que persiste en UTC y devuelve aware. Esto además dejó
   la capa portable a PostgreSQL sin cambios.

2. **"Limitación de SQLite" como comentario.** La IA quería despachar la
   concurrencia con un `# TODO`. Lo rechacé porque la prueba evalúa
   "concurrencia básica" como criterio. Implementé `threading.Lock` por
   `professional_name` con un guard para el dict de locks. Defendible para
   uvicorn con 1 worker, documentado el upgrade a PostgreSQL con `EXCLUDE`.

3. **Comparadores `>` vs `>=` en reembolsos.** El primer borrador usaba `>`
   en algunas franjas. Lo cambié a `>=` deliberadamente porque el límite
   exacto (24h, 4h, 1h) debe favorecer al usuario, y agregué tests
   específicos de los límites exactos para evitar regresiones futuras.

4. **Festivos hardcodeados sin revisión.** La IA generó una lista
   plausible. Verifiqué manualmente contra el calendario oficial (Ley 51 de
   1983) y descubrí en plena ejecución del seed que `2026-06-15` es
   Sagrado Corazón trasladado, no un lunes laboral. Si hubiera confiado
   ciegamente, el seed habría tenido reservas "válidas" en festivo.

5. **`ReservationStatus.COMPLETED`.** Generado por defecto en el enum.
   Nunca se usaba en el flujo del negocio. Lo quité — CLAUDE.md pide
   evitar tanto strings hardcodeados como código muerto.

---

## Cómo se usó Claude en la práctica

- **Pair-programmer**: pedía borradores de módulos completos y los
  revisaba línea por línea ajustando nomenclatura y reglas.
- **Caja de resonancia** para decisiones de diseño (por ejemplo dónde
  vivía la validación de horario: ¿schema, service o util? — terminó en
  un service puro y testeable).
- **Generador de documentación** consistente (README/DOC/NOTAS) a partir
  del código ya estabilizado.
- **Sugerencias de edge cases** que no había considerado (límite exacto
  de 24h, reserva que termina exactamente a las 19:00, datetime naive).

No se aceptó código a ciegas: la prueba de los **21 tests pasando** vino
después de varios ajustes manuales, incluyendo bugs que el primer output
de la IA no detectó (el de timezone con SQLite fue el más serio).

---

## Cómo aplico este mismo flujo en mi trabajo WordPress/PHP diario

El stack de esta prueba es Python, pero el **flujo de trabajo con IA** que
usé aquí es idéntico al que aplico día a día en WordPress, PHP y plugins
de WooCommerce:

- **Generación de hooks y filtros**: pido borradores de `add_action` /
  `add_filter` con la signatura correcta y los reviso contra el codex
  (los nombres y orden de parámetros de hooks de WooCommerce cambian
  entre versiones; siempre verifico).
- **Refactor de plugins legacy**: extraigo lógica acoplada de
  `functions.php` o de templates a clases (`includes/`) usando IA como
  asistente, pero **yo decido la arquitectura** (separación de
  responsabilidades, naming de clases, dónde inyectar dependencias).
- **Revisiones de seguridad**: uso la IA como segundo par de ojos para
  detectar XSS, SQL injection, `nonce` faltantes o falta de
  `current_user_can()`. Pero **el `$wpdb->prepare()` lo escribo yo**
  porque la IA a veces sugiere concatenaciones que parecen seguras y
  no lo son.
- **Generación de tests con WP-CLI / wp-phpunit**: borrador con IA,
  revisión manual de fixtures y aserciones.
- **Integraciones de APIs externas** (como Uber Direct, mi plugin
  `Uber-Direct-Plugin`): IA me ayuda a escribir los wrappers de
  `wp_remote_post`, pero el manejo de errores, retries, idempotencia y
  logging los diseño yo en base a lo que ya falló en producción.
- **Documentación y READMEs de plugins**: igual que este NOTAS.md —
  borrador rápido + revisión exhaustiva contra el código real.

La regla en mi flujo es la misma en ambos stacks: **la IA acelera, pero
la decisión técnica es mía y validada con pruebas reales**.
