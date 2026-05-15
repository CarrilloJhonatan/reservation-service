from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.enums import ReservationStatus
from app.models import Reservation


class ReservationRepository:
    """Acceso a datos para reservas. Sin lógica de negocio."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, reservation_id: int) -> Reservation | None:
        return self.db.get(Reservation, reservation_id)

    def add(self, reservation: Reservation) -> Reservation:
        self.db.add(reservation)
        self.db.flush()
        return reservation

    def count_active_future_by_user(self, user_id: int, now: datetime) -> int:
        stmt = select(Reservation).where(
            and_(
                Reservation.user_id == user_id,
                Reservation.status == ReservationStatus.ACTIVE,
                Reservation.start_time > now,
            )
        )
        return len(list(self.db.execute(stmt).scalars()))

    def find_overlap_for_professional(
        self, professional_name: str, start: datetime, end: datetime
    ) -> Reservation | None:
        """Detecta solapamiento (start < other.end AND end > other.start)."""
        stmt = select(Reservation).where(
            and_(
                Reservation.professional_name == professional_name,
                Reservation.status == ReservationStatus.ACTIVE,
                Reservation.start_time < end,
                Reservation.end_time > start,
            )
        )
        return self.db.execute(stmt).scalars().first()

    def list_by_user_and_range(
        self, user_id: int, range_start: datetime, range_end: datetime
    ) -> list[Reservation]:
        stmt = (
            select(Reservation)
            .where(
                and_(
                    Reservation.user_id == user_id,
                    Reservation.start_time >= range_start,
                    Reservation.start_time <= range_end,
                )
            )
            .order_by(Reservation.start_time.asc())
        )
        return list(self.db.execute(stmt).scalars())
