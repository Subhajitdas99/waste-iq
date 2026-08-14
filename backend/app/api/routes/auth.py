from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, rate_limit
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserRead
from app.services.auth import (
    authenticate_user,
    issue_token_for_user,
    register_user,
    forgot_password,
    reset_password,
)

router = APIRouter()


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return issue_token_for_user(user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/forgot-password", dependencies=[Depends(rate_limit(requests=5, window=60))])
def forgot_password_route(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    forgot_password(db, payload.email, background_tasks)
    return {"message": "If that email exists, we sent a password reset link."}


@router.post("/reset-password", dependencies=[Depends(rate_limit(requests=5, window=60))])
def reset_password_route(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        reset_password(db, payload.token, payload.new_password)
    except ValueError:
        # Generic 400 to avoid leaking token status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid, reused, or expired token."
        )
    return {"message": "Password has been successfully reset."}
