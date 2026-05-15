from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    repo = UserRepository(db)
    user = repo.create(
        name=payload.name, email=payload.email, is_premium=payload.is_premium
    )
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("", response_model=list[UserOut], summary="Listar usuarios")
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in UserRepository(db).list_all()]
