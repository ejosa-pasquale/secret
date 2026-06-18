from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Role, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def authenticate(session: Session, email: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.email == email.lower().strip(), User.is_active.is_(True)))
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_user(session: Session, full_name: str, email: str, password: str, role: Role = Role.customer) -> User:
    existing = session.scalar(select(User).where(User.email == email.lower().strip()))
    if existing:
        raise ValueError("Email già registrata")
    user = User(full_name=full_name.strip(), email=email.lower().strip(), password_hash=hash_password(password), role=role)
    session.add(user)
    session.flush()
    return user


def can_manage_restaurant(role: str) -> bool:
    return role in {Role.admin.value, Role.restaurant.value}
