from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, *, name: str, email: str, is_premium: bool) -> User:
        user = User(name=name, email=email, is_premium=is_premium)
        self.db.add(user)
        self.db.flush()
        return user

    def list_all(self) -> list[User]:
        return list(self.db.execute(select(User)).scalars())
