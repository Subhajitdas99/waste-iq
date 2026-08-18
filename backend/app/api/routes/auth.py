from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, ChangePasswordRequest, LoginRequest, RegisterRequest
from app.schemas.user import UserRead
from app.services.auth import (
    authenticate_user,
    change_password as change_password_service,
    get_user_by_email,
    issue_token_for_user,
    register_user,
)
from app.services.audit import AuditService

router = APIRouter()

_audit_service = AuditService()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user = register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return issue_token_for_user(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        # Record the failure before raising so it commits to the database.
        # actor_user_id is set only when the email corresponds to an existing
        # account; no email is stored, so the audit trail leaks no
        # enumeration signal.
        existing_user = get_user_by_email(db, payload.email)
        _audit_service.record(
            db,
            actor_user_id=existing_user.id if existing_user is not None else None,
            action="login_failure",
            resource="user",
            resource_id=str(existing_user.id) if existing_user is not None else None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    _audit_service.record(
        db,
        actor_user_id=user.id,
        action="login_success",
        resource="user",
        resource_id=str(user.id),
    )
    db.commit()
    return issue_token_for_user(user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        change_password_service(
            db,
            current_user,
            payload.current_password,
            payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"message": "Password changed successfully"}
