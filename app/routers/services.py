from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import ServiceCreate, ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


@router.post(
    "",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear servicio",
)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)) -> ServiceOut:
    repo = ServiceRepository(db)
    svc = repo.create(
        name=payload.name,
        duration_minutes=payload.duration_minutes,
        price=payload.price,
        non_refundable=payload.non_refundable,
    )
    db.commit()
    db.refresh(svc)
    return ServiceOut.model_validate(svc)


@router.get("", response_model=list[ServiceOut], summary="Listar servicios")
def list_services(db: Session = Depends(get_db)) -> list[ServiceOut]:
    return [ServiceOut.model_validate(s) for s in ServiceRepository(db).list_all()]
