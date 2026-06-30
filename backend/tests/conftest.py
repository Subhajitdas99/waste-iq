"""
Shared fixtures for the Waste-IQ test suite.

Isolation strategy:
- One in-memory SQLite database is created PER TEST FUNCTION (not shared
  across the session), using StaticPool so the single in-memory connection
  is reused across the request inside that one test instead of vanishing
  between connections (SQLite in-memory DBs are connection-scoped by
  default, which would otherwise destroy data between dependency calls).
- All tables are created fresh at the start of every test and dropped at
  the end. This guarantees zero cross-test leakage without needing
  begin/rollback savepoint tricks, which are more fragile to get right
  across FastAPI's dependency-injected sessions.
- The app's get_db dependency is overridden to yield a session bound to
  this per-test engine, then app.dependency_overrides is cleared after.
- No external services, no production DATABASE_URL is ever touched.

CI / environment note:
`app.core.config.Settings` reads from a hardcoded `.env` file path and
constructs at import time (`settings = get_settings()` in
app/core/config.py). To keep this suite runnable in CI with zero real
secrets, every required env var is set here via os.environ BEFORE any
`app.*` module is imported -- this must happen at module level (not
inside a fixture), since pytest collects and imports all test files,
which transitively import app.main, before any fixture has a chance
to run.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_unused.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("ADMIN_REGISTRATION_CODE", "test-admin-code")
# Bootstrap admin vars intentionally left unset so bootstrap_admin_user()
# is a no-op during tests (it returns early if any of the four are missing).

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.main import app as fastapi_app
from app.models.base import Base
from app.models.user import User, UserRole

# Import every model module so Base.metadata is fully populated before
# create_all() runs. SQLAlchemy only registers a model with the metadata
# once its module has been imported somewhere in the process.
from app.models import user  # noqa: F401
from app.models import pickup_request  # noqa: F401
from app.models import pickup_request_event  # noqa: F401
from app.models import collector_assignment  # noqa: F401
from app.models import dealer_profile  # noqa: F401
from app.models import material_category  # noqa: F401
from app.models import pricing_rule  # noqa: F401
from app.models import inventory_lot  # noqa: F401
from app.models import inventory_lot_event  # noqa: F401  # noqa: F401


@pytest.fixture()
def db_session():
    """
    Fresh in-memory SQLite database for a single test. Tables are created
    before the test runs and the whole engine is discarded after, so no
    state survives between tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """
    TestClient wired to the same db_session used by the test.
    """

    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    try:
        with TestClient(fastapi_app) as test_client:
            yield test_client
    finally:
        fastapi_app.dependency_overrides.clear()        

    


    


# ─── User factories ───────────────────────────────────────────────────────────


def _create_user(db_session, *, role: UserRole, email: str, name: str = "Test User", phone: str = "9000000001") -> User:
    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password("Test@1234"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def citizen_user(db_session) -> User:
    return _create_user(db_session, role=UserRole.citizen, email="citizen@test.com", phone="9000000001")


@pytest.fixture()
def collector_user(db_session) -> User:
    return _create_user(db_session, role=UserRole.collector, email="collector@test.com", phone="9000000002")


@pytest.fixture()
def dealer_user(db_session) -> User:
    return _create_user(db_session, role=UserRole.dealer, email="dealer@test.com", phone="9000000003")


@pytest.fixture()
def admin_user(db_session) -> User:
    return _create_user(db_session, role=UserRole.admin, email="admin@test.com", phone="9000000004")


@pytest.fixture()
def second_dealer_user(db_session) -> User:
    return _create_user(db_session, role=UserRole.dealer, email="dealer2@test.com", phone="9000000005")


@pytest.fixture()
def citizen_headers(citizen_user) -> dict[str, str]:
    return _auth_headers(citizen_user)


@pytest.fixture()
def collector_headers(collector_user) -> dict[str, str]:
    return _auth_headers(collector_user)


@pytest.fixture()
def dealer_headers(dealer_user) -> dict[str, str]:
    return _auth_headers(dealer_user)


@pytest.fixture()
def admin_headers(admin_user) -> dict[str, str]:
    return _auth_headers(admin_user)


@pytest.fixture()
def second_dealer_headers(second_dealer_user) -> dict[str, str]:
    return _auth_headers(second_dealer_user)


# ─── Approved dealer profile fixture ─────────────────────────────────────────


@pytest.fixture()
def approved_dealer_profile(db_session, dealer_user):
    """An APPROVED dealer profile for dealer_user, created directly via the model."""
    from app.models.dealer_profile import DealerProfile, DealerVerificationStatus

    profile = DealerProfile(
        user_id=dealer_user.id,
        business_name="Test Recyclers Pvt Ltd",
        owner_name="Dealer Owner",
        phone="9000000003",
        address="123 Industrial Area, Kolkata",
        city="Kolkata",
        pincode="700001",
        materials_accepted=["PET Plastic", "Cardboard"],
        verification_status=DealerVerificationStatus.approved,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture()
def pending_dealer_profile(db_session, dealer_user):
    """A PENDING (unapproved) dealer profile."""
    from app.models.dealer_profile import DealerProfile, DealerVerificationStatus

    profile = DealerProfile(
        user_id=dealer_user.id,
        business_name="Pending Recyclers",
        owner_name="Pending Owner",
        phone="9000000003",
        address="456 Pending Lane, Kolkata",
        city="Kolkata",
        pincode="700002",
        materials_accepted=["E-Waste"],
        verification_status=DealerVerificationStatus.pending,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


# ─── Material category + pricing rule fixtures ───────────────────────────────


@pytest.fixture()
def material_category(db_session):
    from app.models.material_category import MaterialCategory

    category = MaterialCategory(
        code="PET_PLASTIC",
        name="PET Plastic",
        description="Bottles and containers",
        is_active=True,
        display_order=1,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture()
def active_pricing_rule(db_session, material_category, admin_user):
    from app.models.pricing_rule import PricingRule

    rule = PricingRule(
        material_category_id=material_category.id,
        city="Kolkata",
        unit_price_per_kg=12.50,
        currency_code="INR",
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=1),
        effective_to=None,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


# ─── Completed pickup + assignment fixture (for inventory lot eligibility) ──


@pytest.fixture()
def completed_pickup_with_assignment(db_session, citizen_user, collector_user):
    """
    A pickup request in `completed` status with a CollectorAssignment that
    has a positive weight_kg — i.e. eligible for inventory lot creation.
    """
    from app.models.pickup_request import PickupRequest, PickupStatus
    from app.models.collector_assignment import CollectorAssignment

    pickup = PickupRequest(
        user_id=citizen_user.id,
        waste_type="Plastic bottles",
        address="12 Lake Road, Kolkata, 700029",
        latitude=22.5726,
        longitude=88.3639,
        status=PickupStatus.completed,
    )
    db_session.add(pickup)
    db_session.flush()

    assignment = CollectorAssignment(
        request_id=pickup.id,
        collector_id=collector_user.id,
        accepted_at=datetime.now(timezone.utc) - timedelta(hours=2),
        completed_at=datetime.now(timezone.utc),
        weight_kg=15.5,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(pickup)
    return pickup


@pytest.fixture()
def inventory_lot(db_session, completed_pickup_with_assignment, material_category, active_pricing_rule, admin_user):
    """A persisted, available, visible InventoryLot ready to be browsed/reserved."""
    from app.models.inventory_lot import InventoryLot, InventoryLotStatus, InventoryLotVisibility

    lot = InventoryLot(
        lot_number="LOT-2026-000001",
        pickup_request_id=completed_pickup_with_assignment.id,
        citizen_id=completed_pickup_with_assignment.user_id,
        collector_id=completed_pickup_with_assignment.assignment.collector_id,
        material_category_id=material_category.id,
        material_description="Plastic bottles",
        weight_kg=15.5,
        unit_price_per_kg_snapshot=12.50,
        total_listed_amount=193.75,
        pricing_rule_id=active_pricing_rule.id,
        source_city="Kolkata",
        source_address_snapshot=completed_pickup_with_assignment.address,
        status=InventoryLotStatus.available,
        visibility=InventoryLotVisibility.visible,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)
    return lot