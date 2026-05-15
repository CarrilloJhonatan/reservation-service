# CLAUDE.md

> Este archivo contiene las instrucciones de proyecto que uso con **Claude Code**
> (Anthropic) para mantener consistencia técnica durante el desarrollo.
> Documenta convenciones, arquitectura y reglas de negocio que la IA debe
> respetar al generar o modificar código. Es la forma estándar de dirigir a
> Claude Code en un proyecto y refleja mi flujo de trabajo con IA como apoyo
> real (no como sustituto del criterio técnico). Ver `NOTAS.md` para casos
> concretos de uso y rechazo de sugerencias durante esta prueba.

## Contexto del Proyecto

Este proyecto es una prueba técnica para un sistema de gestión de reservas utilizando FastAPI, SQLite y SQLAlchemy.

La prioridad del proyecto NO es complejidad arquitectónica extrema, sino:

* claridad
* mantenibilidad
* buenas prácticas
* separación de responsabilidades
* capacidad de defender decisiones técnicas en entrevista

La solución debe sentirse profesional, limpia y pragmática.

---

# Stack Tecnológico

* Python 3.12+
* FastAPI
* SQLite
* SQLAlchemy ORM
* Pydantic
* pytest

---

# Objetivos de Arquitectura

Mantener separación clara entre:

* routers → manejo HTTP
* services → lógica de negocio
* repositories → acceso a datos
* models → entidades ORM
* schemas → validación y serialización
* utils → helpers reutilizables

Los routers NO deben contener lógica de negocio compleja.

---

# Filosofía del Proyecto

Este proyecto prioriza:

* simplicidad profesional
* claridad
* código defendible en entrevista
* facilidad de mantenimiento
* tipado fuerte
* edge cases importantes
* manejo correcto de fechas y timezone

Evitar sobreingeniería.

---

# Reglas Importantes

## Timezone

Toda fecha debe manejarse usando:

```python
from zoneinfo import ZoneInfo
```

Timezone oficial:

```python
America/Bogota
```

Nunca usar datetimes naive.

---

# Reglas de Negocio Críticas

* No reservas domingo
* No reservas festivos Colombia 2026
* Horario permitido:

  * 7:00 AM a 7:00 PM
* Mínimo 2 horas de anticipación
* Máximo 3 reservas activas futuras por usuario
* No permitir solapamiento por profesional
* Servicios non_refundable nunca generan reembolso

---

# Clean Code

## Preferir:

* funciones pequeñas
* nombres descriptivos
* tipado fuerte
* lógica explícita
* validaciones claras

## Evitar:

* lógica duplicada
* lógica compleja en routers
* queries SQL embebidas innecesariamente
* strings mágicos
* lógica mezclada entre capas

---

# Enums

Usar enums para estados:

```python
ACTIVE
CANCELLED
```

Evitar strings hardcodeados.

---

# Services

Toda lógica importante debe vivir en services.

Ejemplos:

* cálculo de reembolsos
* validación de horarios
* validación de conflictos
* validación de límites

---

# Repositories

Repositories deben encargarse únicamente de:

* consultas
* inserciones
* actualizaciones
* acceso ORM

NO deben contener lógica de negocio compleja.

---

# Manejo de Errores

Usar excepciones personalizadas:

* BookingConflictError
* InvalidBookingTimeError
* RefundNotAllowedError

Las respuestas HTTP deben ser consistentes.

---

# Testing

Los tests deben enfocarse en:

* edge cases reales
* reglas de negocio
* timezone
* límites exactos
* conflictos de reservas

No escribir tests triviales.

---

# Logging

Mantener logging simple y profesional:

* logs en consola
* logs en archivo
* eventos importantes
* errores relevantes

---

# Estilo Esperado

El código debe sentirse:

* profesional
* limpio
* mantenible
* fácil de explicar
* preparado para crecer

Evitar complejidad innecesaria.

---

# Objetivo Final

La solución debe demostrar:

* criterio técnico
* experiencia backend real
* capacidad de organización
* comprensión de arquitectura
* uso inteligente de IA como herramienta de productividad
