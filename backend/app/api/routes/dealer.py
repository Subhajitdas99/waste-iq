from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.dealer import DealerProfileCreate, DealerProfileRead, DealerProfileUpdate
from app.services.dealer_profiles import (
    create_dealer_profile,
    get_dealer_profile,
    update_dealer_profile,
)

router = APIRouter()


@router.post("/profile", response_model=DealerProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: DealerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    return create_dealer_profile(db, current_user, payload)


@router.get("/profile", response_model=DealerProfileRead)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    profile = get_dealer_profile(db, current_user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
        )
    return profile


@router.patch("/profile", response_model=DealerProfileRead)
def patch_profile(
    payload: DealerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    profile = update_dealer_profile(db, current_user, payload)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
        )
    return profile
