from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collector_location import CollectorLocation, CollectorLocationHistory


class CollectorLocationRepository:
    def get_latest(self, db: Session, collector_id: int) -> CollectorLocation | None:
        return db.scalar(
            select(CollectorLocation).where(CollectorLocation.collector_id == collector_id)
        )

    def upsert_latest(
        self,
        db: Session,
        collector_id: int,
        latitude: float,
        longitude: float,
        accuracy: float | None,
    ) -> CollectorLocation:
        """Replace (or create) the collector's latest location row."""
        location = self.get_latest(db, collector_id)
        if location is None:
            location = CollectorLocation(
                collector_id=collector_id,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(location)
        else:
            location.latitude = latitude
            location.longitude = longitude
            location.accuracy = accuracy
            location.updated_at = datetime.now(timezone.utc)
        db.flush()
        return location

    def add_history(
        self,
        db: Session,
        collector_id: int,
        latitude: float,
        longitude: float,
        accuracy: float | None,
    ) -> CollectorLocationHistory:
        entry = CollectorLocationHistory(
            collector_id=collector_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.flush()
        return entry

    def list_history(
        self,
        db: Session,
        collector_id: int,
        limit: int = 50,
    ) -> list[CollectorLocationHistory]:
        return list(
            db.scalars(
                select(CollectorLocationHistory)
                .where(CollectorLocationHistory.collector_id == collector_id)
                .order_by(CollectorLocationHistory.recorded_at.desc())
                .limit(limit)
            )
        )
