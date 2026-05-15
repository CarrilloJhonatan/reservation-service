# NOTAS.md — Uso de IA durante el desarrollo

Este documento es transparente sobre el uso de **Claude** como herramienta de
productividad durante la implementación de la prueba técnica.

---

## Qué partes fueron generadas con IA

Claude colaboró en:

- **Estructura inicial del proyecto** (layout de carpetas y archivos).
- **Boilerplate** de SQLAlchemy 2.x (declarative base + `Mapped`),
  Pydantic v2 schemas, routers FastAPI.
- **Primer borrador** de la lógica de validación de horarios y del cálculo
  de reembolsos.
- **Tests iniciales** con pytest y fixtures.
- **Redacción de README, DOC.md y este archivo.**

---

## Qué fue ajustado / revisado manualmente

- **Reglas de negocio**: validé que la matriz de reembolso (estándar y
  premium) coincide con el enunciado, en particular los límites exactos
  (24h, 4h, 1h). Confirmé que `>=` es el comparador correcto en cada
  franja.
- **Timezone**: forcé que la API rechace datetimes naive en el schema y
  en `ensure_aware_bogota`, para evitar el bug clásico de "8am UTC vs
  8am Bogotá".
- **Festivos 2026**: revisé manualmente la lista contra el calendario
  oficial (Ley 51 de 1983) y los traslados aplicables.
- **Concurrencia**: dejé explícita la limitación de SQLite (no soporta
  `FOR UPDATE`) y documenté en el README la estrategia para PostgreSQL
  con `EXCLUDE` + `tstzrange`.
- **Manejo de errores**: extendí la jerarquía con `NotFoundError` y
  `ReservationLimitExceededError` para no abusar de los códigos 400/422.
- **Seed**: introduje datos inconsistentes a propósito (email inválido,
  precio negativo, duración cero, espacios sobrantes) para mostrar
  sanitización defensiva en `seed.py`.

---

## Decisiones tomadas

1. **Capas explícitas** (router/service/repository) sin caer en patrones
   pesados (no hay Unit of Work, no hay DTOs separados de schemas).
   Justificación: la prueba pide claridad y separación, no DDD.
2. **`StrEnum` para estados**: persistencia simple en SQLite y serialización
   nativa.
3. **`init_db()` con `create_all`** en lugar de Alembic: para una prueba
   técnica añade complejidad sin valor. Documenté la migración a Alembic
   como mejora futura.
4. **Exception handler global** en lugar de `try/except` en cada router:
   más DRY y consistente.
5. **No agregué autenticación**: el enunciado lo prohíbe explícitamente
   ("autenticación compleja: NO") y desviaría el foco.
6. **Logging con `RotatingFileHandler`** de la stdlib: sin dependencias
   adicionales como `loguru`.

---

## Cómo se utilizó Claude

- **Como pair-programmer**: pedía borradores de módulos completos y luego
  los revisaba línea por línea, ajustando nomenclatura y reglas.
- **Como caja de resonancia** para decisiones de diseño (p.ej. dónde
  vivía la validación de horario: ¿schema, service o util? — terminó en
  un service puro y testeable).
- **Para redactar documentación** consistente (README/DOC) a partir del
  código ya implementado.
- **Para sugerir edge cases de tests** que no había considerado
  (p.ej. límite exacto de 24h o reserva que termina exactamente a las
  19:00).

No se aceptó código de Claude a ciegas: cada bloque se validó contra el
CLAUDE.md, contra el enunciado y contra los tests.
