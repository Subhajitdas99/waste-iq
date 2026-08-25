from typing import Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.ratelimit import check_rate_limit
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.audit import LoginHistoryEntryRead, LoginHistoryPageRead
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
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
from app.services.email_verification import (
    complete_verification_email_delivery,
    EmailVerificationError,
    verify_email as verify_email_service,
)
from app.services.refresh_token import InvalidRefreshTokenError, RefreshTokenService

router = APIRouter()

_audit_service = AuditService()
_refresh_token_service = RefreshTokenService()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AuthResponse:
    check_rate_limit(request, "register")
    try:
        user = register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    # Deliver the verification email off the request path (WIQ-V1-021) so
    # SMTP I/O never blocks the response. Delivery failure never fails
    # registration: it is logged and the user can resend later.
    background_tasks.add_task(complete_verification_email_delivery, user.id)
    return issue_token_for_user(db, user)


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
    return issue_token_for_user(db, user)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Exchange a refresh token for a fresh access + refresh token pair.

    The presented token is rotated: it is revoked and a new one is issued in
    the same family. Replaying an already-rotated token revokes the family.
    Requires no Authorization header.
    """
    try:
        new_refresh_token, _row, user = _refresh_token_service.rotate(db, payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    return AuthResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=new_refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/verify-email")
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Verify an account's email with a signed one-time token (WIQ-V1-014).

    Public. Invalid, expired, malformed, and stale tokens all produce the
    same generic 400 response so the endpoint cannot be used to enumerate
    accounts. Re-verifying an already verified account is idempotent.
    """
    try:
        message, _newly_verified = verify_email_service(db, payload.token)
    except EmailVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"message": message}


@router.post("/resend-verification")
def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Resend the verification email for an unverified account.

    Public and rate-limited per IP. The response is identical whether or
    not the email is registered (and whether or not it is already verified),
    so the endpoint cannot be used for account or email enumeration. Any
    delivery is dispatched as a background task off the request path.
    """
    check_rate_limit(request, "resend_verification")
    user = get_user_by_email(db, normalize_email(payload.email))
    if user is not None and not user.email_verified:
        background_tasks.add_task(complete_verification_email_delivery, user.id)
    return {
        "message": "If the email is registered and unverified, a verification email has been sent."
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Revoke the current session's refresh token. Idempotent."""
    _refresh_token_service.revoke(db, payload.refresh_token, user_id=current_user.id)
    return None


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Revoke every refresh session of the authenticated user."""
    _refresh_token_service.revoke_all_for_user(db, current_user.id)
    return None


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/login-history", response_model=LoginHistoryPageRead)
def my_login_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    outcome: Literal["success", "failure"] | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoginHistoryPageRead:
    """Recent login attempts for the authenticated user (WIQ-V1-019).

    Identity comes exclusively from the access token — there is deliberately
    no user/actor query parameter, so a caller can only ever read their own
    history. Failures are not attributed to a cause (wrong password, locked
    account, unknown email all surface as plain ``failure``).
    """
    items, total_items, total_pages = _audit_service.login_history(
        db,
        actor_user_id=current_user.id,
        outcome=outcome,
        page=page,
        page_size=page_size,
    )
    return LoginHistoryPageRead(
        items=[LoginHistoryEntryRead.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


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
            payload.refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"message": "Password changed successfully"}
