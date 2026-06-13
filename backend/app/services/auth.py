from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.schemas.auth import AuthResponse, RegisterRequest


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, payload: RegisterRequest) -> User:
    role = payload.role.strip().lower()
    if role not in {UserRole.citizen.value, UserRole.collector.value, UserRole.admin.value}:
        raise ValueError("Role must be citizen, collector, or admin")

    if role == UserRole.admin.value:
        if not settings.admin_registration_code or payload.admin_code != settings.admin_registration_code:
            raise ValueError("Invalid admin registration code")

    user = User(
        name=payload.name.strip(),
        email=normalize_email(payload.email),
        phone=payload.phone.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole(role),
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Email or phone is already registered") from exc

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    statement = select(User).where(User.email == normalize_email(email))
    user = db.execute(statement).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def issue_token_for_user(user: User) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(str(user.id)), user=user)


def bootstrap_admin_user() -> None:
    if not all(
        [
            settings.bootstrap_admin_name,
            settings.bootstrap_admin_email,
            settings.bootstrap_admin_phone,
            settings.bootstrap_admin_password,
        ]
    ):
        return

    db = SessionLocal()
    try:
        existing = db.execute(
            select(User).where(User.email == normalize_email(settings.bootstrap_admin_email))
        ).scalar_one_or_none()
        if existing is not None:
            return

        admin = User(
            name=settings.bootstrap_admin_name.strip(),
            email=normalize_email(settings.bootstrap_admin_email),
            phone=settings.bootstrap_admin_phone.strip(),
            password_hash=hash_password(settings.bootstrap_admin_password),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
    except (OperationalError, ProgrammingError):
        db.rollback()
    finally:
        db.close()
