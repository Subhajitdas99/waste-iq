import abc
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.pickup_request import PickupRequest, PickupStatus
from app.models.user import User, UserRole
from app.schemas.communication import ContactSessionRead
from app.services.audit import AuditService

_ELIGIBLE_COMMUNICATION_STATUSES = {
    PickupStatus.accepted,
    PickupStatus.on_the_way,
    PickupStatus.collected,
}


class MaskedCommunicationProvider(abc.ABC):
    """Abstract interface for privacy-preserving masked communication providers."""

    @abc.abstractmethod
    def initiate_contact(
        self, pickup_request: PickupRequest, requester: User, recipient: User | None
    ) -> ContactSessionRead:
        """Establish a masked contact session between participants."""
        pass


class MockMaskedCommunicationProvider(MaskedCommunicationProvider):
    """Development and testing mock provider clearly marked as non-production.

    Generates synthetic session metadata without accessing real telephony or exposing real PII.
    """

    def initiate_contact(
        self, pickup_request: PickupRequest, requester: User, recipient: User | None
    ) -> ContactSessionRead:
        session_id = f"mock-session-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        masked_number = f"+1-800-555-0199 (Ext #{pickup_request.id})"
        instructions = (
            "Contact is routed privately through Waste-IQ. "
            "Your real phone number will remain private."
        )

        return ContactSessionRead(
            session_id=session_id,
            pickup_id=pickup_request.id,
            status="initiated",
            masked_number=masked_number,
            instructions=instructions,
            expires_at=expires_at,
        )


class DisabledMaskedCommunicationProvider(MaskedCommunicationProvider):
    """Provider for environments where masked communication is explicitly disabled."""

    def initiate_contact(
        self, pickup_request: PickupRequest, requester: User, recipient: User | None
    ) -> ContactSessionRead:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Masked communication service is currently unavailable",
        )


class TwilioMaskedCommunicationProvider(MaskedCommunicationProvider):
    """Production Twilio Proxy / Masked Voice adapter (stub for production activation)."""

    def __init__(self, api_key: str | None, service_sid: str | None) -> None:
        self.api_key = api_key
        self.service_sid = service_sid

    def initiate_contact(
        self, pickup_request: PickupRequest, requester: User, recipient: User | None
    ) -> ContactSessionRead:
        if not self.api_key or not self.service_sid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Production communication provider is not configured properly",
            )
        # Production integration point for Twilio Proxy / Voice API
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Production telephony provider integration pending API key configuration",
        )


def get_communication_provider(
    settings: Settings = get_settings(),
) -> MaskedCommunicationProvider:
    provider_name = settings.communication_provider.lower()
    if provider_name == "mock":
        return MockMaskedCommunicationProvider()
    elif provider_name == "twilio":
        return TwilioMaskedCommunicationProvider(
            api_key=settings.communication_provider_api_key,
            service_sid=settings.communication_provider_service_sid,
        )
    else:
        return DisabledMaskedCommunicationProvider()


class CommunicationService:
    """Application-level communication authorization boundary and service."""

    def __init__(
        self,
        provider: MaskedCommunicationProvider | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._provider = provider
        self._audit_service = audit_service or AuditService()

    def _get_provider(self) -> MaskedCommunicationProvider:
        if self._provider is not None:
            return self._provider
        return get_communication_provider()

    def initiate_masked_contact(
        self, db: Session, pickup_id: int, requester: User
    ) -> ContactSessionRead:
        # Load pickup request
        pickup_request = db.get(PickupRequest, pickup_id)
        if pickup_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Pickup request not found"
            )

        # Verify role & ownership / assignment authorization
        requester_role = getattr(requester.role, "value", str(requester.role))
        is_admin = requester_role == UserRole.admin.value
        is_citizen_owner = requester.id == pickup_request.user_id
        is_assigned_collector = (
            requester_role == UserRole.collector.value
            and pickup_request.assignment is not None
            and pickup_request.assignment.collector_id == requester.id
        )

        if not (is_admin or is_citizen_owner or is_assigned_collector):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to contact participants for this pickup request",
            )

        # Lifecycle check
        if pickup_request.status == PickupStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No collector has been assigned to this pickup request yet",
            )

        if pickup_request.status not in _ELIGIBLE_COMMUNICATION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact is no longer active for completed or cancelled pickup requests",
            )

        # Determine recipient
        recipient: User | None = None
        if is_citizen_owner:
            if pickup_request.assignment is not None:
                recipient = pickup_request.assignment.collector
        elif is_assigned_collector:
            recipient = pickup_request.citizen
        elif is_admin:
            recipient = pickup_request.citizen

        provider = self._get_provider()
        session = provider.initiate_contact(pickup_request, requester, recipient)

        # Audit logging (sanitized, zero PII)
        self._audit_service.record(
            db,
            actor_user_id=requester.id,
            action="communication_requested",
            resource="pickup_request",
            resource_id=str(pickup_request.id),
            after={
                "session_id": session.session_id,
                "requester_role": requester_role,
                "status": session.status,
            },
        )
        db.commit()

        return session
