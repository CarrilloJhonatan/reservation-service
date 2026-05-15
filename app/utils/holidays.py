"""Festivos Colombia 2026 (hardcoded).

Para producción se recomendaría calcular los festivos móviles según la ley
de Lunes Festivo (51 de 1983) o usar un paquete como `holidays`, pero para
esta prueba mantenerlos hardcoded es explícito y defendible.
"""
from datetime import date

COLOMBIA_HOLIDAYS_2026: frozenset[date] = frozenset(
    {
        date(2026, 1, 1),   # Año Nuevo
        date(2026, 1, 12),  # Reyes Magos (trasladado)
        date(2026, 3, 23),  # San José (trasladado)
        date(2026, 4, 2),   # Jueves Santo
        date(2026, 4, 3),   # Viernes Santo
        date(2026, 5, 1),   # Día del Trabajo
        date(2026, 5, 18),  # Ascensión (trasladado)
        date(2026, 6, 8),   # Corpus Christi (trasladado)
        date(2026, 6, 15),  # Sagrado Corazón (trasladado)
        date(2026, 6, 29),  # San Pedro y San Pablo (trasladado)
        date(2026, 7, 20),  # Independencia
        date(2026, 8, 7),   # Batalla de Boyacá
        date(2026, 8, 17),  # Asunción (trasladado)
        date(2026, 10, 12), # Día de la Raza
        date(2026, 11, 2),  # Todos los Santos (trasladado)
        date(2026, 11, 16), # Independencia de Cartagena (trasladado)
        date(2026, 12, 8),  # Inmaculada Concepción
        date(2026, 12, 25), # Navidad
    }
)


def is_colombian_holiday(d: date) -> bool:
    return d in COLOMBIA_HOLIDAYS_2026
