from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.ratelimit import check_rate_limit
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, ChangePasswordRequest, LoginRequest, RegisterRequest
from app.schemas.user import UserRead
from app.services.auth import (
    change_password as change_password_service,
    get_user_by_email,
    issue_token_for_user,
    normalize_email,
    record_failed_login,
    register_user,
    reset_login_failures,
)
from app.services.audit import AuditService

router = APIRouter()

_audit_service = AuditService()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    check_rate_limit(request, "register")
    try:
        user = register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return issue_token_for_user(user)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    email = normalize_email(payload.email)

    # Rate limit by IP and by account before any credential work. The account
    # key is tracked for every attempt (existing account or not) so the 429
    # response cannot be used to enumerate accounts.
    check_rate_limit(request, "login", account_identifier=email)

    user = get_user_by_email(db, email)

    if user is None or user.is_locked():
        # Locked accounts and unknown emails respond identically so lockout
        # state cannot be used to enumerate accounts. Locked accounts are
        # rejected without touching the failure counter.
        _audit_service.record(
            db,
            actor_user_id=user.id if user is not None else None,
            action="login_failure",
            resource="user",
            resource_id=str(user.id) if user is not None else None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not verify_password(payload.password, user.password_hash):
        record_failed_login(db, user)
        _audit_service.record(
            db,
            actor_user_id=user.id,
            action="login_failure",
            resource="user",
            resource_id=str(user.id),
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    reset_login_failures(db, user)
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
