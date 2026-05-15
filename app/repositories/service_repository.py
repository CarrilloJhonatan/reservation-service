from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Service


class ServiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, service_id: int) -> Service | None:
        return self.db.get(Service, service_id)

    def create(
        self, *, name: str, duration_minutes: int, price: float, non_refundable: bool
    ) -> Service:
        svc = Service(
            name=name,
            duration_minutes=duration_minutes,
            price=price,
            non_refundable=non_refundable,
        )
        self.db.add(svc)
        self.db.flush()
        return svc

    def list_all(self) -> list[Service]:
        return list(self.db.execute(select(Service)).scalars())
