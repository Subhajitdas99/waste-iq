import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.schemas.auth import AuthResponse, RegisterRequest
from app.schemas.user import UserRead

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == normalize_email(email))).scalar_one_or_none()


def register_user(db: Session, payload: RegisterRequest) -> User:
    role = payload.role.strip().lower()
    try:
        role_enum = UserRole(role)
    except ValueError:
        raise ValueError("Role must be citizen, collector, dealer, or admin") from None

    if role_enum == UserRole.admin:
        if (
            not settings.admin_registration_code
            or payload.admin_code != settings.admin_registration_code
        ):
            raise ValueError("Invalid admin registration code")

    user = User(
        name=payload.name.strip(),
        email=normalize_email(payload.email),
        phone=payload.phone.strip(),
        password_hash=hash_password(payload.password),
        role=role_enum,
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
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    if not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")
    if verify_password(new_password, user.password_hash):
        raise ValueError("New password must be different from the current password")

    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def issue_token_for_user(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(str(user.id)), user=UserRead.model_validate(user)
    )


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

    admin_name = settings.bootstrap_admin_name
    admin_email = settings.bootstrap_admin_email
    admin_phone = settings.bootstrap_admin_phone
    admin_password = settings.bootstrap_admin_password
    assert admin_name is not None
    assert admin_email is not None
    assert admin_phone is not None
    assert admin_password is not None

    db = SessionLocal()
    try:
        existing = get_user_by_email(db, admin_email)
        if existing is not None:
            return

        admin = User(
            name=admin_name.strip(),
            email=normalize_email(admin_email),
            phone=admin_phone.strip(),
            password_hash=hash_password(admin_password),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
    except (OperationalError, ProgrammingError):
        db.rollback()
        logger.warning("Admin bootstrap skipped: database schema is not ready.", exc_info=True)
    finally:
        db.close()
