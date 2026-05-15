from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.reservation import (
    CancellationOut,
    ReservationCreate,
    ReservationOut,
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post(
    "",
    response_model=ReservationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva",
    description=(
        "Crea una reserva validando horario (L–S, 07:00–19:00 hora Bogotá), "
        "festivos Colombia 2026, anticipación mínima de 2h, máximo 3 reservas "
        "activas por usuario y solapamiento del profesional."
    ),
    responses={
        409: {"description": "Conflicto de solapamiento o límite excedido."},
        422: {"description": "Horario inválido."},
        404: {"description": "Usuario o servicio no encontrado."},
    },
)
def create_reservation(
    payload: ReservationCreate, db: Session = Depends(get_db)
) -> ReservationOut:
    reservation = BookingService(db).create_reservation(payload)
    return ReservationOut.model_validate(reservation)


@router.post(
    "/{reservation_id}/cancel",
    response_model=CancellationOut,
    summary="Cancelar reserva",
    description=(
        "Cancela la reserva y calcula reembolso según política "
        "(estándar/premium/non_refundable)."
    ),
    responses={
        404: {"description": "Reserva no encontrada."},
        409: {"description": "Reserva ya cancelada o ya iniciada."},
    },
)
def cancel_reservation(
    reservation_id: int, db: Session = Depends(get_db)
) -> CancellationOut:
    reservation, refund = BookingService(db).cancel_reservation(reservation_id)
    return CancellationOut(
        reservation_id=reservation.id,
        status=reservation.status,
        refund_amount=refund,
        message="Reserva cancelada correctamente.",
    )


@router.get(
    "",
    response_model=list[ReservationOut],
    summary="Listar reservas por usuario y rango",
)
def list_reservations(
    user_id: int = Query(..., gt=0),
    start: datetime = Query(..., description="ISO 8601 con timezone"),
    end: datetime = Query(..., description="ISO 8601 con timezone"),
    db: Session = Depends(get_db),
) -> list[ReservationOut]:
    rs = BookingService(db).list_user_reservations(user_id, start, end)
    return [ReservationOut.model_validate(r) for r in rs]
