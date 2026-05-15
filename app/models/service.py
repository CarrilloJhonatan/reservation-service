from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # Numeric para preservar precisión de precios; SQLite lo trata como REAL.
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    non_refundable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
