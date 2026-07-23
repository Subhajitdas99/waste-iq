from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.dealer_profile import DealerProfile, DealerVerificationStatus
from app.models.user import User, UserRole
from app.schemas.dealer import (
    AdminDealerSummaryRead,
    DealerProfileCreate,
    DealerProfileRead,
    DealerProfileUpdate,
    DealerVerificationActionRead,
)

PROFILE_REQUIRED_FIELDS = (
    "business_name",
    "owner_name",
    "phone",
    "address",
    "city",
    "pincode",
    "materials_accepted",
)


def _dealer_profile_query():
    return select(DealerProfile).options(selectinload(DealerProfile.user))


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


def _calculate_profile_completion(profile: DealerProfile | None) -> int:
    if profile is None:
        return 0

    completed_fields = 0
    for field in PROFILE_REQUIRED_FIELDS:
        value = getattr(profile, field)
        if isinstance(value, list):
            if value:
                completed_fields += 1
        elif value:
            completed_fields += 1

    return round((completed_fields / len(PROFILE_REQUIRED_FIELDS)) * 100)


def _to_profile_schema(profile: DealerProfile) -> DealerProfileRead:
    return DealerProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        business_name=profile.business_name,
        owner_name=profile.owner_name,
        phone=profile.phone,
        address=profile.address,
        city=profile.city,
        pincode=profile.pincode,
        gst_number=profile.gst_number,
        license_number=profile.license_number,
        materials_accepted=list(profile.materials_accepted),
        verification_status=profile.verification_status.value,
        approved_at=profile.approved_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        profile_completion=_calculate_profile_completion(profile),
    )


def _to_admin_summary(user: User) -> AdminDealerSummaryRead:
    profile = user.dealer_profile
    return AdminDealerSummaryRead(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        account_phone=user.phone,
        has_profile=profile is not None,
        business_name=profile.business_name if profile is not None else None,
        owner_name=profile.owner_name if profile is not None else None,
        city=profile.city if profile is not None else None,
        pincode=profile.pincode if profile is not None else None,
        materials_accepted=list(profile.materials_accepted) if profile is not None else [],
        verification_status=(
            profile.verification_status.value
            if profile is not None
            else DealerVerificationStatus.pending.value
        ),
        approved_at=profile.approved_at if profile is not None else None,
        profile_completion=_calculate_profile_completion(profile),
        created_at=profile.created_at if profile is not None else user.created_at,
    )


def _get_profile_model_for_user(db: Session, user_id: int) -> DealerProfile | None:
    return db.execute(
        _dealer_profile_query().where(DealerProfile.user_id == user_id)
    ).scalar_one_or_none()


def get_dealer_profile(db: Session, dealer: User) -> DealerProfileRead | None:
    profile = _get_profile_model_for_user(db, dealer.id)
    if profile is None:
        return None
    return _to_profile_schema(profile)


def create_dealer_profile(
    db: Session, dealer: User, payload: DealerProfileCreate
) -> DealerProfileRead:
    if dealer.role != UserRole.dealer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only dealers can create dealer profiles"
        )

    existing = _get_profile_model_for_user(db, dealer.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Dealer profile already exists"
        )

    data = payload.model_dump(mode="json")
    data["materials_accepted"] = _normalize_materials(data["materials_accepted"])
    profile = DealerProfile(user_id=dealer.id, **data)
    db.add(profile)
    db.commit()
    created_profile = _get_profile_model_for_user(db, dealer.id)
    assert created_profile is not None
    return _to_profile_schema(created_profile)


def update_dealer_profile(
    db: Session, dealer: User, payload: DealerProfileUpdate
) -> DealerProfileRead | None:
    profile = _get_profile_model_for_user(db, dealer.id)
    if profile is None:
        return None

    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if "materials_accepted" in update_data:
        update_data["materials_accepted"] = _normalize_materials(update_data["materials_accepted"])

    for field, value in update_data.items():
        setattr(profile, field, value)

    if update_data and profile.verification_status != DealerVerificationStatus.pending:
        profile.verification_status = DealerVerificationStatus.pending
        profile.approved_at = None

    db.commit()
    profile = _get_profile_model_for_user(db, dealer.id)
    assert profile is not None
    return _to_profile_schema(profile)


def list_dealers_for_admin(db: Session) -> list[AdminDealerSummaryRead]:
    statement = (
        select(User)
        .options(selectinload(User.dealer_profile))
        .where(User.role == UserRole.dealer)
        .order_by(User.created_at.desc())
    )
    users = db.execute(statement).scalars().all()
    return [_to_admin_summary(user) for user in users]


def approve_dealer_profile(db: Session, dealer_user_id: int) -> DealerVerificationActionRead:
    profile = _get_profile_model_for_user(db, dealer_user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
        )

    profile.verification_status = DealerVerificationStatus.approved
    profile.approved_at = datetime.now(timezone.utc)
    db.commit()
    return DealerVerificationActionRead(
        user_id=profile.user_id,
        verification_status=profile.verification_status.value,
        approved_at=profile.approved_at,
    )


def reject_dealer_profile(db: Session, dealer_user_id: int) -> DealerVerificationActionRead:
    profile = _get_profile_model_for_user(db, dealer_user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
        )

    profile.verification_status = DealerVerificationStatus.rejected
    profile.approved_at = None
    db.commit()
    return DealerVerificationActionRead(
        user_id=profile.user_id,
        verification_status=profile.verification_status.value,
        approved_at=profile.approved_at,
    )
