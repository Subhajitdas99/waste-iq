from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dealer_profile import DealerApprovalStatus, DealerProfile
from app.models.dealer_profile_event import DealerProfileEvent
from app.models.user import User
from app.repositories.dealer_profiles import DealerProfileRepository
from app.schemas.dealer import (
    AdminDealerDetailRead,
    AdminDealerListPageRead,
    AdminDealerSummaryRead,
    DealerApprovalActionRead,
    DealerApprovalEventRead,
    DealerProfileRead,
)

# Allowed approval workflow transitions. Editing a profile always moves it
# back to `draft` so the updated business information can be reviewed again.
ALLOWED_TRANSITIONS: dict[DealerApprovalStatus, frozenset[DealerApprovalStatus]] = {
    DealerApprovalStatus.draft: frozenset({DealerApprovalStatus.submitted}),
    DealerApprovalStatus.submitted: frozenset(
        {
            DealerApprovalStatus.draft,
            DealerApprovalStatus.approved,
            DealerApprovalStatus.rejected,
        }
    ),
    DealerApprovalStatus.approved: frozenset({DealerApprovalStatus.draft}),
    DealerApprovalStatus.rejected: frozenset(
        {DealerApprovalStatus.draft, DealerApprovalStatus.submitted}
    ),
}

PROFILE_COMPLETION_FIELDS = (
    "business_name",
    "owner_name",
    "phone",
    "address",
    "city",
    "postal_code",
    "materials_accepted",
)


def validate_approval_transition(
    current: DealerApprovalStatus, target: DealerApprovalStatus
) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid approval status transition from " f"'{current.value}' to '{target.value}'"
            ),
        )


def is_dealer_approved(db: Session, dealer: User) -> bool:
    profile = DealerProfileRepository().get_by_user_id(db, dealer.id)
    return profile is not None and profile.approval_status == DealerApprovalStatus.approved


def _calculate_profile_completion(profile: DealerProfile) -> int:
    completed_fields = 0
    for field in PROFILE_COMPLETION_FIELDS:
        value = getattr(profile, field)
        if isinstance(value, list):
            if value:
                completed_fields += 1
        elif value:
            completed_fields += 1
    return round((completed_fields / len(PROFILE_COMPLETION_FIELDS)) * 100)


def _to_profile_schema(profile: DealerProfile) -> DealerProfileRead:
    return DealerProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        business_name=profile.business_name,
        owner_name=profile.owner_name,
        phone=profile.phone,
        email=profile.email,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        postal_code=profile.postal_code,
        gst_number=profile.gst_number,
        license_number=profile.license_number,
        business_type=profile.business_type,
        profile_image=profile.profile_image,
        description=profile.description,
        materials_accepted=list(profile.materials_accepted),
        approval_status=profile.approval_status,
        rejection_reason=profile.rejection_reason,
        is_verified=profile.is_verified,
        approved_at=profile.approved_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        profile_completion=_calculate_profile_completion(profile),
    )


def _to_admin_summary(profile: DealerProfile) -> AdminDealerSummaryRead:
    user = profile.user
    return AdminDealerSummaryRead(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        account_phone=user.phone,
        has_profile=True,
        business_name=profile.business_name,
        owner_name=profile.owner_name,
        city=profile.city,
        postal_code=profile.postal_code,
        materials_accepted=list(profile.materials_accepted),
        approval_status=profile.approval_status,
        rejected_reason=profile.rejection_reason,
        approved_at=profile.approved_at,
        profile_completion=_calculate_profile_completion(profile),
        created_at=user.created_at,
    )


def _to_event_schema(event: DealerProfileEvent) -> DealerApprovalEventRead:
    actor = event.actor
    return DealerApprovalEventRead(
        id=event.id,
        status=event.status,
        note=event.note,
        actor_name=actor.name if actor is not None else None,
        actor_role=actor.role.value if actor is not None else None,
        created_at=event.created_at,
    )


def _to_action_schema(profile: DealerProfile) -> DealerApprovalActionRead:
    return DealerApprovalActionRead(
        profile_id=profile.id,
        user_id=profile.user_id,
        approval_status=profile.approval_status,
        rejection_reason=profile.rejection_reason,
        is_verified=profile.is_verified,
        approved_at=profile.approved_at,
        updated_at=profile.updated_at,
    )


class AdminDealerApprovalService:
    def __init__(self, repository: DealerProfileRepository | None = None) -> None:
        self._repository = repository or DealerProfileRepository()

    def list_dealers(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        status_value: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> AdminDealerListPageRead:
        parsed_status = None
        if status_value:
            try:
                parsed_status = DealerApprovalStatus(status_value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid approval status filter",
                )

        items, total_items, total_pages = self._repository.list_profiles(
            db,
            page=page,
            page_size=page_size,
            status=parsed_status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return AdminDealerListPageRead(
            items=[_to_admin_summary(item) for item in items],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def list_pending_dealers(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> AdminDealerListPageRead:
        items, total_items, total_pages = self._repository.list_pending(
            db, page=page, page_size=page_size, search=search
        )
        return AdminDealerListPageRead(
            items=[_to_admin_summary(item) for item in items],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    def get_dealer_detail(self, db: Session, dealer_user_id: int) -> AdminDealerDetailRead:
        profile = self._get_profile_by_user_id_or_404(db, dealer_user_id)
        user = profile.user
        events = self._repository.list_events(db, profile.id)
        return AdminDealerDetailRead(
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            account_phone=user.phone,
            profile=_to_profile_schema(profile),
            timeline=[_to_event_schema(event) for event in events],
        )

    def approve_dealer(
        self, db: Session, admin: User, dealer_user_id: int
    ) -> DealerApprovalActionRead:
        profile = self._get_profile_by_user_id_or_404(db, dealer_user_id)
        validate_approval_transition(profile.approval_status, DealerApprovalStatus.approved)

        profile.approval_status = DealerApprovalStatus.approved
        profile.approved_at = datetime.now(timezone.utc)
        profile.is_verified = True
        profile.rejection_reason = None
        self._repository.add_event(
            db, profile, status=DealerApprovalStatus.approved, note="Profile approved.", actor=admin
        )
        return _to_action_schema(self._repository.save(db, profile))

    def reject_dealer(
        self, db: Session, admin: User, dealer_user_id: int, reason: str
    ) -> DealerApprovalActionRead:
        profile = self._get_profile_by_user_id_or_404(db, dealer_user_id)
        validate_approval_transition(profile.approval_status, DealerApprovalStatus.rejected)

        profile.approval_status = DealerApprovalStatus.rejected
        profile.rejection_reason = reason
        profile.approved_at = None
        profile.is_verified = False
        self._repository.add_event(
            db,
            profile,
            status=DealerApprovalStatus.rejected,
            note=f"Profile rejected: {reason}",
            actor=admin,
        )
        return _to_action_schema(self._repository.save(db, profile))

    def _get_profile_by_user_id_or_404(self, db: Session, dealer_user_id: int) -> DealerProfile:
        profile = self._repository.get_by_user_id(db, dealer_user_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dealer profile not found"
            )
        return profile
