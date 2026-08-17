from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dealer_profile import DealerApprovalStatus, DealerProfile
from app.models.user import User, UserRole
from app.repositories.dealer_profiles import DealerProfileRepository
from app.schemas.dealer import (
    DealerApprovalEventRead,
    DealerProfileCreate,
    DealerProfileRead,
    DealerProfileUpdate,
)
from app.services.dealer_approval import (
    _to_event_schema,
    _to_profile_schema,
    is_dealer_approved,
    validate_approval_transition,
)
from app.services.notifications import NotificationDispatcher


class DealerProfileService:
    def __init__(self, repository: DealerProfileRepository | None = None) -> None:
        self._repository = repository or DealerProfileRepository()
        self._dispatcher = NotificationDispatcher()

    def get_profile(self, db: Session, dealer: User) -> DealerProfileRead | None:
        profile = self._repository.get_by_user_id(db, dealer.id)
        if profile is None:
            return None
        return _to_profile_schema(profile)

    def get_timeline(self, db: Session, dealer: User) -> list[DealerApprovalEventRead]:
        profile = self._repository.get_by_user_id(db, dealer.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
            )
        events = self._repository.list_events(db, profile.id)
        return [_to_event_schema(event) for event in events]

    def create_profile(
        self, db: Session, dealer: User, payload: DealerProfileCreate
    ) -> DealerProfileRead:
        if dealer.role != UserRole.dealer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only dealers can create dealer profiles",
            )

        existing = self._repository.get_by_user_id(db, dealer.id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Dealer profile already exists"
            )

        data = payload.model_dump(mode="python")
        self._validate_unique_identifiers(db, dealer.id, data)
        data["email"] = data.get("email") or dealer.email
        data["materials_accepted"] = _normalize_materials(data["materials_accepted"])

        profile = DealerProfile(user_id=dealer.id, **data)
        db.add(profile)
        db.flush()
        self._repository.add_event(
            db, profile, status=DealerApprovalStatus.draft, note="Profile created.", actor=dealer
        )
        return _to_profile_schema(self._repository.save(db, profile))

    def update_profile(
        self, db: Session, dealer: User, payload: DealerProfileUpdate
    ) -> DealerProfileRead | None:
        profile = self._repository.get_by_user_id(db, dealer.id)
        if profile is None:
            return None

        update_data = payload.model_dump(exclude_unset=True, mode="python")
        self._validate_unique_identifiers(db, dealer.id, update_data)
        if "materials_accepted" in update_data:
            update_data["materials_accepted"] = _normalize_materials(
                update_data["materials_accepted"]
            )

        for field, value in update_data.items():
            setattr(profile, field, value)

        if profile.approval_status != DealerApprovalStatus.draft:
            validate_approval_transition(profile.approval_status, DealerApprovalStatus.draft)
            profile.approval_status = DealerApprovalStatus.draft
            profile.rejection_reason = None
            profile.approved_at = None
            profile.is_verified = False
            self._repository.add_event(
                db,
                profile,
                status=DealerApprovalStatus.draft,
                note="Profile updated and reset to draft for review.",
                actor=dealer,
            )

        return _to_profile_schema(self._repository.save(db, profile))

    def submit_profile(self, db: Session, dealer: User) -> DealerProfileRead:
        profile = self._repository.get_by_user_id(db, dealer.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
            )

        validate_approval_transition(profile.approval_status, DealerApprovalStatus.submitted)

        profile.approval_status = DealerApprovalStatus.submitted
        profile.rejection_reason = None
        self._repository.add_event(
            db,
            profile,
            status=DealerApprovalStatus.submitted,
            note="Profile submitted for review.",
            actor=dealer,
        )
        self._dispatcher.notify_dealer_profile_submitted(db, profile)
        return _to_profile_schema(self._repository.save(db, profile))

    def is_approved(self, db: Session, dealer: User) -> bool:
        return is_dealer_approved(db, dealer)

    def _validate_unique_identifiers(self, db: Session, dealer_id: int, data: dict) -> None:
        gst_number = data.get("gst_number")
        if gst_number and self._repository.gst_number_exists(db, gst_number, dealer_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="GST number is already registered to another dealer",
            )
        license_number = data.get("license_number")
        if license_number and self._repository.license_number_exists(db, license_number, dealer_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="License number is already registered to another dealer",
            )


def _normalize_materials(materials: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for item in materials:
        value = item.strip()
        key = value.lower()
        if value and key not in seen:
            normalized.append(value)
            seen.add(key)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one accepted material is required",
        )
    return normalized
