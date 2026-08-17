import math
from typing import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.dealer_profile import DealerApprovalStatus, DealerProfile
from app.models.dealer_profile_event import DealerProfileEvent
from app.models.user import User

SORTABLE_FIELDS = {
    "created_at": DealerProfile.created_at,
    "updated_at": DealerProfile.updated_at,
    "business_name": DealerProfile.business_name,
    "city": DealerProfile.city,
}


class DealerProfileRepository:
    def base_query(self) -> Select[tuple[DealerProfile]]:
        return select(DealerProfile).options(selectinload(DealerProfile.user))

    def get_by_user_id(self, db: Session, user_id: int) -> DealerProfile | None:
        statement = self.base_query().where(DealerProfile.user_id == user_id)
        return db.execute(statement).scalar_one_or_none()

    def get_by_id(self, db: Session, profile_id: int) -> DealerProfile | None:
        statement = self.base_query().where(DealerProfile.id == profile_id)
        return db.execute(statement).scalar_one_or_none()

    def get_by_id_with_events(self, db: Session, profile_id: int) -> DealerProfile | None:
        statement = (
            self.base_query()
            .where(DealerProfile.id == profile_id)
            .options(selectinload(DealerProfile.events).selectinload(DealerProfileEvent.actor))
        )
        return db.execute(statement).scalar_one_or_none()

    def save(self, db: Session, profile: DealerProfile) -> DealerProfile:
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def list_profiles(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        status: DealerApprovalStatus | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[Sequence[DealerProfile], int, int]:
        statement = self.base_query().join(User, User.id == DealerProfile.user_id)

        if status is not None:
            statement = statement.where(DealerProfile.approval_status == status)
        if search:
            like = f"%{search.lower()}%"
            statement = statement.where(
                or_(
                    func.lower(DealerProfile.business_name).like(like),
                    func.lower(DealerProfile.owner_name).like(like),
                    func.lower(User.email).like(like),
                )
            )

        count_statement = select(func.count()).select_from(statement.subquery())
        total_items = db.scalar(count_statement) or 0
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        sort_column = SORTABLE_FIELDS.get(sort_by, DealerProfile.created_at)
        order = sort_column.desc() if sort_order == "desc" else sort_column.asc()
        statement = (
            statement.order_by(order, DealerProfile.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = db.execute(statement).unique().scalars().all()

        return items, total_items, total_pages

    def list_pending(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[Sequence[DealerProfile], int, int]:
        return self.list_profiles(
            db,
            page=page,
            page_size=page_size,
            status=DealerApprovalStatus.submitted,
            search=search,
            sort_by="updated_at",
            sort_order="desc",
        )

    def list_events(self, db: Session, profile_id: int) -> list[DealerProfileEvent]:
        statement = (
            select(DealerProfileEvent)
            .where(DealerProfileEvent.profile_id == profile_id)
            .options(selectinload(DealerProfileEvent.actor))
            .order_by(
                DealerProfileEvent.created_at.desc(),
                DealerProfileEvent.id.desc(),
            )
        )
        return list(db.execute(statement).scalars().all())

    def add_event(
        self,
        db: Session,
        profile: DealerProfile,
        *,
        status: DealerApprovalStatus,
        note: str,
        actor: User | None = None,
    ) -> DealerProfileEvent:
        event = DealerProfileEvent(
            profile_id=profile.id,
            actor_user_id=actor.id if actor is not None else None,
            status=status,
            note=note,
        )
        db.add(event)
        db.flush()
        return event

    def gst_number_exists(
        self, db: Session, gst_number: str, exclude_user_id: int | None = None
    ) -> bool:
        statement = select(DealerProfile.id).where(DealerProfile.gst_number == gst_number)
        if exclude_user_id is not None:
            statement = statement.where(DealerProfile.user_id != exclude_user_id)
        return db.scalar(statement) is not None

    def license_number_exists(
        self, db: Session, license_number: str, exclude_user_id: int | None = None
    ) -> bool:
        statement = select(DealerProfile.id).where(DealerProfile.license_number == license_number)
        if exclude_user_id is not None:
            statement = statement.where(DealerProfile.user_id != exclude_user_id)
        return db.scalar(statement) is not None
