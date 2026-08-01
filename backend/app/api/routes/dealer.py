from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.models.user import User
from app.schemas.dealer import (
    DealerApprovalEventRead,
    DealerProfileCreate,
    DealerProfileRead,
    DealerProfileUpdate,
)
from app.schemas.dealer_inventory import (
    DealerInventoryCreate,
    DealerInventoryPageRead,
    DealerInventoryRead,
    DealerInventoryUpdate,
)
from app.services.dealer_profiles import DealerProfileService
from app.services.dealer_inventory import (
    create_dealer_inventory,
    delete_dealer_inventory,
    get_dealer_inventory,
    list_dealer_inventories,
    mark_inventory_sold,
    release_inventory,
    reserve_inventory,
    update_dealer_inventory,
)

router = APIRouter()

_dealer_profile_service = DealerProfileService()


@router.post("/profile", response_model=DealerProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: DealerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    return _dealer_profile_service.create_profile(db, current_user, payload)


@router.get("/profile", response_model=DealerProfileRead)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    profile = _dealer_profile_service.get_profile(db, current_user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
        )
    return profile


@router.put("/profile", response_model=DealerProfileRead)
@router.patch("/profile", response_model=DealerProfileRead)
def update_profile(
    payload: DealerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    profile = _dealer_profile_service.update_profile(db, current_user, payload)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
        )
    return profile


@router.post("/profile/submit", response_model=DealerProfileRead)
def submit_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerProfileRead:
    return _dealer_profile_service.submit_profile(db, current_user)


@router.get("/profile/timeline", response_model=list[DealerApprovalEventRead])
def get_profile_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> list[DealerApprovalEventRead]:
    return _dealer_profile_service.get_timeline(db, current_user)


@router.get("/inventory", response_model=DealerInventoryPageRead)
def list_inventory(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryPageRead:
    return list_dealer_inventories(
        db, current_user, page=page, page_size=page_size, status_filter=status_filter
    )


@router.get("/inventory/{inventory_id}", response_model=DealerInventoryRead)
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryRead:
    return get_dealer_inventory(db, current_user, inventory_id)


@router.post(
    "/inventory",
    response_model=DealerInventoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    payload: DealerInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryRead:
    return create_dealer_inventory(db, current_user, payload)


@router.put("/inventory/{inventory_id}", response_model=DealerInventoryRead)
def update_inventory(
    inventory_id: int,
    payload: DealerInventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryRead:
    return update_dealer_inventory(db, current_user, inventory_id, payload)


@router.delete("/inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> None:
    delete_dealer_inventory(db, current_user, inventory_id)


@router.post("/inventory/{inventory_id}/reserve", response_model=DealerInventoryRead)
def reserve(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryRead:
    return reserve_inventory(db, current_user, inventory_id)


@router.post("/inventory/{inventory_id}/release", response_model=DealerInventoryRead)
def release(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryRead:
    return release_inventory(db, current_user, inventory_id)


@router.post("/inventory/{inventory_id}/mark-sold", response_model=DealerInventoryRead)
def mark_sold(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("dealer")),
) -> DealerInventoryRead:
    return mark_inventory_sold(db, current_user, inventory_id)
