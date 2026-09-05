"""PostgreSQL concurrency tests for WIQ-V1-053.

These tests verify that PostgreSQL row-level locking correctly serializes
concurrent confirm/dispute operations on the same pickup request.

Run with:

    pytest tests/postgres/ -v -m postgres

The tests require a reachable PostgreSQL instance.
"""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.base import Base
from app.models.collector_assignment import CollectorAssignment
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User, UserRole
from app.repositories.pickup_requests import PickupRequestRepository
from app.services.pickup_requests import confirm_pickup_weight, dispute_pickup_weight

pytestmark = pytest.mark.postgres


_engine = None
_session_factory = None


def _pg_engine():
    global _engine

    if _engine is None:
        _engine = create_engine(
            get_settings().database_url,
            poolclass=NullPool,
            pool_pre_ping=True,
            future=True,
            connect_args={"connect_timeout": 10},
        )

    return _engine


def _pg_session_factory():
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=_pg_engine(),
            autoflush=False,
            autocommit=False,
            future=True,
        )

    return _session_factory


@pytest.fixture(scope="module")
def _pg_reachable():
    """Skip the PostgreSQL suite when the configured database is unavailable."""
    engine = _pg_engine()

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        database_url = get_settings().database_url
        redacted = database_url.split("@")[0] + "@*:*/*" if "@" in database_url else database_url

        pytest.skip(
            f"PostgreSQL is not reachable at {redacted!r}: "
            f"{type(exc).__name__}: {exc}. "
            "Start PostgreSQL and re-run the tests."
        )

    yield


@pytest.fixture
def schema(_pg_reachable):
    """Ensure the PostgreSQL test database has the application schema.

    Uses drop/create on the specific tables needed by these tests to
    guarantee the correct column types from the current model definition.
    """
    engine = _pg_engine()

    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS collector_assignments CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pickup_requests CASCADE"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    yield


def _uid() -> str:
    return uuid.uuid4().hex[:10]


@pytest.fixture
def pg_pickup(schema):
    """Create an isolated weight-recorded pickup for a concurrency test."""
    factory = _pg_session_factory()
    session: Session = factory()

    citizen = User(
        name="WIQ053 Citizen",
        email=f"c_{_uid()}@wiq053.test",
        phone=f"99{_uid()[:7]}01",
        password_hash=hash_password("Test@1234"),
        role=UserRole.citizen,
        email_verified_at=datetime.now(timezone.utc),
    )

    collector = User(
        name="WIQ053 Collector",
        email=f"cl_{_uid()}@wiq053.test",
        phone=f"99{_uid()[:7]}02",
        password_hash=hash_password("Test@1234"),
        role=UserRole.collector,
        email_verified_at=datetime.now(timezone.utc),
    )

    session.add_all([citizen, collector])
    session.flush()

    pickup = PickupRequest(
        user_id=citizen.id,
        waste_type="Plastic bottles",
        address="5 Test Rd",
        latitude=22.5726,
        longitude=88.3639,
        status=PickupStatus.weight_recorded,
    )

    session.add(pickup)
    session.flush()

    assignment = CollectorAssignment(
        request_id=pickup.id,
        collector_id=collector.id,
        accepted_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        weight_kg=8.5,
    )

    session.add(assignment)
    session.commit()

    pickup_id = pickup.id
    citizen_id = citizen.id
    collector_id = collector.id

    yield citizen, collector, pickup_id

    try:
        session.execute(
            text("DELETE FROM pickup_disputes WHERE request_id = :request_id"),
            {"request_id": pickup_id},
        )
        session.execute(
            text("DELETE FROM collector_assignments " "WHERE request_id = :request_id"),
            {"request_id": pickup_id},
        )
        session.execute(
            text("DELETE FROM pickup_requests " "WHERE id = :request_id"),
            {"request_id": pickup_id},
        )
        session.execute(
            text("DELETE FROM users " "WHERE id IN (:citizen_id, :collector_id)"),
            {
                "citizen_id": citizen_id,
                "collector_id": collector_id,
            },
        )
        session.commit()
    finally:
        session.close()


def test_select_for_update_blocks_second_transaction(
    pg_pickup,
    _pg_reachable,
):
    """Verify PostgreSQL FOR UPDATE blocks a second transaction."""
    _, _, pickup_id = pg_pickup

    factory = _pg_session_factory()

    lock_acquired = threading.Event()
    release_lock = threading.Event()
    second_attempt_started = threading.Event()
    second_completed = threading.Event()

    first_error: list[Exception] = []
    second_error: list[Exception] = []

    def first_transaction():
        session: Session = factory()

        try:
            session.begin()

            pickup = PickupRequestRepository().get_by_id_with_dispute_for_update(
                session,
                pickup_id,
            )

            assert pickup is not None

            lock_acquired.set()

            if not release_lock.wait(timeout=10):
                raise AssertionError("Timed out waiting to release PostgreSQL lock")

            session.rollback()
        except Exception as exc:
            first_error.append(exc)
            lock_acquired.set()
        finally:
            session.close()

    def second_transaction():
        session: Session = factory()

        try:
            second_attempt_started.set()
            session.begin()

            pickup = PickupRequestRepository().get_by_id_with_dispute_for_update(
                session,
                pickup_id,
            )

            assert pickup is not None
            session.rollback()
        except Exception as exc:
            second_error.append(exc)
        finally:
            second_completed.set()
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(first_transaction)

        assert lock_acquired.wait(timeout=10), "First transaction did not acquire SELECT FOR UPDATE"

        assert not first_error, f"First transaction failed: {first_error}"

        second_future = pool.submit(second_transaction)

        assert second_attempt_started.wait(timeout=10), "Second transaction did not start"

        # The first transaction still owns the row lock, so the second
        # transaction must remain blocked.
        assert not second_completed.wait(timeout=1), (
            "Second SELECT FOR UPDATE completed while the first transaction "
            "still held the row lock"
        )

        release_lock.set()

        done, _ = wait(
            [first_future, second_future],
            timeout=10,
        )

        assert len(done) == 2, "PostgreSQL concurrency workers did not finish"

        first_future.result()
        second_future.result()

    assert not first_error, f"First transaction failed: {first_error}"
    assert not second_error, f"Second transaction failed: {second_error}"


def test_confirm_and_dispute_are_serialized(
    pg_pickup,
    _pg_reachable,
):
    """Verify confirm and dispute cannot both win the same race."""
    citizen, _, pickup_id = pg_pickup

    barrier = threading.Barrier(2, timeout=10)

    results: dict[str, Exception | None] = {
        "confirm": None,
        "dispute": None,
    }

    def confirm():
        session: Session = _pg_session_factory()()

        try:
            barrier.wait()
            confirm_pickup_weight(session, citizen, pickup_id)
        except Exception as exc:
            results["confirm"] = exc
        finally:
            session.close()

    def dispute():
        session: Session = _pg_session_factory()()

        try:
            barrier.wait()
            dispute_pickup_weight(
                session,
                citizen,
                pickup_id,
                reason="Weight seems off.",
            )
        except Exception as exc:
            results["dispute"] = exc
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(confirm),
            pool.submit(dispute),
        ]

        done, _ = wait(futures, timeout=30)

        assert len(done) == 2, "Confirm/dispute workers did not finish within 30 seconds"

        for future in futures:
            future.result()

    confirm_error = results["confirm"]
    dispute_error = results["dispute"]

    confirm_won = confirm_error is None
    dispute_won = dispute_error is None

    assert confirm_won != dispute_won, (
        "Exactly one of confirm/dispute must win the race: "
        f"confirm={confirm_error!r}, dispute={dispute_error!r}"
    )

    loser_error = dispute_error if confirm_won else confirm_error

    assert isinstance(loser_error, HTTPException), (
        f"Expected the losing operation to raise HTTPException, "
        f"got {type(loser_error).__name__}: {loser_error!r}"
    )

    assert loser_error.status_code in (400, 409)

    assert not isinstance(
        loser_error, (ValueError, TypeError)
    ), f"Unexpected application error: {loser_error!r}"

    verify_session: Session = _pg_session_factory()()

    try:
        pickup = verify_session.get(PickupRequest, pickup_id)

        assert pickup is not None

        expected_status = PickupStatus.completed if confirm_won else PickupStatus.disputed

        assert pickup.status == expected_status
    finally:
        verify_session.close()


def test_no_integrity_error_leaks_to_caller(
    pg_pickup,
    _pg_reachable,
):
    """Verify a confirm/dispute race never exposes a DB IntegrityError."""
    citizen, _, pickup_id = pg_pickup

    barrier = threading.Barrier(2, timeout=10)
    errors: list[Exception] = []

    def confirm():
        session: Session = _pg_session_factory()()

        try:
            barrier.wait()
            confirm_pickup_weight(session, citizen, pickup_id)
        except Exception as exc:
            errors.append(exc)
        finally:
            session.close()

    def dispute():
        session: Session = _pg_session_factory()()

        try:
            barrier.wait()
            dispute_pickup_weight(
                session,
                citizen,
                pickup_id,
                reason="Concurrent dispute",
            )
        except Exception as exc:
            errors.append(exc)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(confirm),
            pool.submit(dispute),
        ]

        done, _ = wait(futures, timeout=30)

        assert len(done) == 2

        for future in futures:
            future.result()

    database_error_names = {
        "IntegrityError",
        "DataError",
        "ProgrammingError",
    }

    leaked_errors = [exc for exc in errors if type(exc).__name__ in database_error_names]

    assert not leaked_errors, "Database-level errors leaked to the caller: " f"{leaked_errors!r}"

    verify_session: Session = _pg_session_factory()()

    try:
        pickup = verify_session.get(PickupRequest, pickup_id)

        assert pickup is not None
        assert pickup.status in {
            PickupStatus.completed,
            PickupStatus.disputed,
        }
    finally:
        verify_session.close()


def test_duplicate_dispute_idempotent(
    pg_pickup,
    _pg_reachable,
):
    """Verify repeating the same dispute is idempotent."""
    citizen, _, pickup_id = pg_pickup

    factory = _pg_session_factory()

    session: Session = factory()

    try:
        first = dispute_pickup_weight(
            session,
            citizen,
            pickup_id,
            reason="Same reason.",
        )

        assert first.status == "disputed"
    finally:
        session.close()

    session = factory()

    try:
        second = dispute_pickup_weight(
            session,
            citizen,
            pickup_id,
            reason="Same reason.",
        )

        assert second.status == "disputed"
    finally:
        session.close()

    session = factory()

    try:
        with pytest.raises(HTTPException) as exc_info:
            dispute_pickup_weight(
                session,
                citizen,
                pickup_id,
                reason="Different reason.",
            )

        assert exc_info.value.status_code == 409
    finally:
        session.close()


def test_confirm_is_idempotent(
    pg_pickup,
    _pg_reachable,
):
    """Verify repeating confirmation of a completed pickup is idempotent."""
    citizen, _, pickup_id = pg_pickup

    factory = _pg_session_factory()

    session: Session = factory()

    try:
        first = confirm_pickup_weight(
            session,
            citizen,
            pickup_id,
        )

        assert first.status == "completed"
    finally:
        session.close()

    session = factory()

    try:
        second = confirm_pickup_weight(
            session,
            citizen,
            pickup_id,
        )

        assert second.status == "completed"
    finally:
        session.close()
