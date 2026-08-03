from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus

PAGE_SIZE_MAX = 50


class NotificationRepository:
    def create(self, db: Session, notification: Notification) -> Notification:
        db.add(notification)
        db.flush()
        return notification

    def get_for_user(self, db: Session, user_id: int, notification_id: int) -> Notification | None:
        statement = self.base_query_for_user(user_id).where(Notification.id == notification_id)
        return db.execute(statement).scalar_one_or_none()

    def base_query_for_user(self, user_id: int) -> Select[tuple[Notification]]:
        return select(Notification).where(Notification.user_id == user_id)

    def list_for_user(
        self,
        db: Session,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        status_value: NotificationStatus | None = None,
    ) -> tuple[list[Notification], int, int]:
        statement = self.base_query_for_user(user_id)
        if status_value is not None:
            statement = statement.where(Notification.status == status_value)

        count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total_items = db.scalar(count_statement) or 0
        total_pages = (total_items + page_size - 1) // page_size if total_items else 0

        items = (
            db.execute(
                statement.order_by(Notification.created_at.desc(), Notification.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return list(items), total_items, total_pages

    def list_unread(self, db: Session, user_id: int, *, limit: int = 50) -> list[Notification]:
        statement = (
            self.base_query_for_user(user_id)
            .where(Notification.status == NotificationStatus.unread)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
        )
        return list(db.execute(statement).scalars().all())

    def count_unread(self, db: Session, user_id: int) -> int:
        statement = self.base_query_for_user(user_id).where(
            Notification.status == NotificationStatus.unread
        )
        return db.scalar(select(func.count()).select_from(statement.subquery())) or 0

    def mark_read(self, db: Session, notification: Notification) -> Notification:
        db.execute(
            update(Notification)
            .where(Notification.id == notification.id)
            .values(status=NotificationStatus.read, read_at=func.now())
        )
        db.refresh(notification)
        return notification

    def mark_all_read(self, db: Session, user_id: int) -> int:
        result = db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.unread,
            )
            .values(status=NotificationStatus.read, read_at=func.now())
        )
        return result.rowcount or 0

    def delete(self, db: Session, notification: Notification) -> None:
        db.execute(delete(Notification).where(Notification.id == notification.id))

    def delete_read(self, db: Session, user_id: int) -> int:
        result = db.execute(
            delete(Notification).where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.read,
            )
        )
        return result.rowcount or 0
