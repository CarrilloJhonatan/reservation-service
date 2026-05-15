"""Lógica de negocio: crear, cancelar, listar reservas."""
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import MAX_ACTIVE_RESERVATIONS_PER_USER
from app.enums import ReservationStatus
from app.exceptions import (
    BookingConflictError,
    NotFoundError,
    RefundNotAllowedError,
    ReservationLimitExceededError,
)
from app.models import Reservation
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.reservation import ReservationCreate
from app.services.refund_service import calculate_refund
from app.services.validation_service import validate_booking_time
from app.utils.datetime_utils import ensure_aware_bogota, now_bogota

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.services = ServiceRepository(db)
        self.reservations = ReservationRepository(db)

    # -- Crear --------------------------------------------------------------

    def create_reservation(self, payload: ReservationCreate) -> Reservation:
        now = now_bogota()
        user = self.users.get(payload.user_id)
        if user is None:
            raise NotFoundError(f"Usuario {payload.user_id} no encontrado.")
        service = self.services.get(payload.service_id)
        if service is None:
            raise NotFoundError(f"Servicio {payload.service_id} no encontrado.")

        start = ensure_aware_bogota(payload.start_time)
        end = validate_booking_time(start, service.duration_minutes, now)

        # Límite de reservas activas futuras.
        active_count = self.reservations.count_active_future_by_user(user.id, now)
        if active_count >= MAX_ACTIVE_RESERVATIONS_PER_USER:
            raise ReservationLimitExceededError(
                f"El usuario ya tiene {MAX_ACTIVE_RESERVATIONS_PER_USER} reservas activas."
            )

        # Conflicto de profesional.
        # NOTA: SQLite no soporta SELECT ... FOR UPDATE. Esto deja una pequeña ventana
        # de carrera entre el check y el insert. En PostgreSQL se resolvería con
        # SELECT ... FOR UPDATE dentro de una transacción serializable, o con un
        # constraint EXCLUDE usando rangos temporales (btree_gist).
        conflict = self.reservations.find_overlap_for_professional(
            payload.professional_name, start, end
        )
        if conflict is not None:
            raise BookingConflictError(
                f"El profesional ya tiene una reserva entre "
                f"{conflict.start_time.isoformat()} y {conflict.end_time.isoformat()}."
            )

        reservation = Reservation(
            user_id=user.id,
            service_id=service.id,
            professional_name=payload.professional_name,
            start_time=start,
            end_time=end,
            status=ReservationStatus.ACTIVE,
            refund_amount=None,
            created_at=now,
            cancelled_at=None,
        )
        self.reservations.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        logger.info(
            "Reserva creada id=%s user=%s prof=%s start=%s",
            reservation.id, user.id, payload.professional_name, start.isoformat(),
        )
        return reservation

    # -- Cancelar -----------------------------------------------------------

    def cancel_reservation(self, reservation_id: int) -> tuple[Reservation, float]:
        now = now_bogota()
        reservation = self.reservations.get(reservation_id)
        if reservation is None:
            raise NotFoundError(f"Reserva {reservation_id} no encontrada.")

        if reservation.status == ReservationStatus.CANCELLED:
            raise RefundNotAllowedError("La reserva ya está cancelada.")

        # Reservas pasadas no se "cancelan" en el sentido de reembolso.
        if reservation.start_time <= now:
            raise RefundNotAllowedError(
                "No se puede cancelar una reserva que ya inició o finalizó."
            )

        refund = calculate_refund(reservation, now)
        reservation.status = ReservationStatus.CANCELLED
        reservation.cancelled_at = now
        reservation.refund_amount = refund

        self.db.commit()
        self.db.refresh(reservation)
        logger.info(
            "Reserva cancelada id=%s refund=%.2f", reservation.id, refund
        )
        return reservation, refund

    # -- Listar -------------------------------------------------------------

    def list_user_reservations(
        self, user_id: int, range_start: datetime, range_end: datetime
    ) -> list[Reservation]:
        if self.users.get(user_id) is None:
            raise NotFoundError(f"Usuario {user_id} no encontrado.")
        rs = ensure_aware_bogota(range_start)
        re = ensure_aware_bogota(range_end)
        if re < rs:
            re = rs + timedelta(days=1)
        return self.reservations.list_by_user_and_range(user_id, rs, re)
