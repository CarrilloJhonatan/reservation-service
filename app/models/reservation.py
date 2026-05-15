from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import ReservationStatus
from app.models.service import Service
from app.models.user import User


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    professional_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)

    # SQLite no preserva tzinfo: trabajamos siempre en UTC al persistir y
    # convertimos a Bogotá en la capa de aplicación. Ver utils/datetime_utils.
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[ReservationStatus] = mapped_column(
        String(20), nullable=False, default=ReservationStatus.ACTIVE, index=True
    )
    refund_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(User, lazy="joined")
    service: Mapped[Service] = relationship(Service, lazy="joined")

    __table_args__ = (
        Index("ix_reservations_prof_start", "professional_name", "start_time"),
    )
