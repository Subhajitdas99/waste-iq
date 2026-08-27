# WIQ-V1-047 — Masked Citizen–Collector Communication

## 1. Problem
During security audit WIQ-V1-044, exposure of citizen phone numbers in public/collector queues was identified as a P0 security blocker. WIQ-V1-044 redacted `citizen_phone` from public, available, and nearby pickup request views.

However, during active pickups, citizens and collectors need a way to communicate regarding pickup location, timing, and access instructions. Exposing raw, unmasked personal phone numbers creates privacy, safety, and harassment risks for both citizens and collectors.

## 2. Privacy Requirements
- **No Raw Phone Exposure**: Neither citizens nor collectors must receive each other's real phone numbers via the API, database queries exposed to clients, or UI views.
- **Redaction Maintained**: Available, nearby, and unassigned pickup views must continue to redact `citizen_phone` to `null`. Assigned collector detail views must also not receive plaintext citizen phone numbers.
- **Masked Boundary**: All direct contact must be mediated through an application-level masked communication boundary.
- **Lifecycle Scoping**: Communication must only be permitted during active, accepted pickup assignments (`accepted`, `on_the_way`, `collected`).

## 3. Threat Model
- **IDOR / BOLA (Insecure Direct Object Reference)**: An attacker attempts to call `POST /pickup-requests/{id}/contact` for a pickup they do not own or are not assigned to.
- **Harvesting / Scraping**: A collector accepts and cancels pickups or queries endpoints to scrape phone numbers.
- **Post-Lifecycle Contact**: A participant attempts to contact another party after a pickup is `completed` or `cancelled`.
- **Log Leakage**: Telephony credentials, session tokens, or phone numbers being logged in audit logs, Sentry, or application stdout.

### Controls Implemented
- Strict authorization checks: Only verified citizen owners, assigned collectors, or admins can call the contact endpoint.
- Pickup lifecycle validation: Denies contact for `pending`, `completed`, or `cancelled` pickups.
- Audit log sanitization (`SENSITIVE_KEYS` expanded to cover `phone`, `citizen_phone`, `collector_phone`, `masked_phone`, `provider_token`, `api_key`).
- Abstracted `MaskedCommunicationProvider` ensuring mock and production modes return synthetic or proxy session metadata only.

## 4. Architecture
The communication boundary acts as a proxy between participants:

```
[ Citizen ] ─── (POST /pickup-requests/{id}/contact) ───► [ Waste-IQ API ]
                                                                 │
                                                       (Masked Communication)
                                                       (  Provider Adapter  )
                                                                 │
[ Collector ] ◄── (Private Masked Proxy Session) ────────────────┘
```

1. **Client** requests contact session via `POST /pickup-requests/{id}/contact`.
2. **Backend API** authenticates JWT, checks email verification, loads pickup, and verifies active ownership/assignment.
3. **Communication Service** delegates to `MaskedCommunicationProvider`.
4. **Provider Adapter** generates masked contact session details (proxy phone number / session ID / instructions).
5. **Audit Log** records a sanitized `communication_requested` event.
6. **Client UI** displays privacy callout and proxy contact session without showing real phone numbers.

## 5. API Behavior

### Endpoint
`POST /pickup-requests/{id}/contact`

### Request Headers
`Authorization: Bearer <JWT_ACCESS_TOKEN>`

### Authorization Policies
- Requester must be authenticated and email-verified (`require_verified_user`).
- Requester must be either:
  - The citizen owner (`pickup.user_id == requester.id`), OR
  - The assigned collector (`pickup.assignment.collector_id == requester.id`), OR
  - An admin user.

### Response Schema (`ContactSessionRead`)
```json
{
  "session_id": "mock-session-a1b2c3d4e5f6",
  "pickup_id": 42,
  "status": "initiated",
  "masked_number": "+1-800-555-0199 (Ext #42)",
  "instructions": "Contact is routed privately through Waste-IQ. Your real phone number will remain private.",
  "expires_at": "2026-08-27T12:05:45Z"
}
```

### Error Responses
- `401 Unauthorized`: Missing or invalid JWT credentials.
- `403 Forbidden`: Unverified email, or requester is not the citizen owner / assigned collector.
- `404 Not Found`: Pickup request does not exist.
- `400 Bad Request`: Pickup request is unassigned (`pending`), or no longer active (`completed`/`cancelled`).
- `503 Service Unavailable`: Communication provider is explicitly disabled via configuration.

## 6. Authorization Rules
| Participant | Pickup Status | Action | Result |
|---|---|---|---|
| Citizen Owner | `accepted` / `on_the_way` / `collected` | Initiate Contact | `200 OK` (Masked Session) |
| Assigned Collector | `accepted` / `on_the_way` / `collected` | Initiate Contact | `200 OK` (Masked Session) |
| Admin | `accepted` / `on_the_way` / `collected` | Initiate Contact | `200 OK` (Masked Session) |
| Citizen Owner | `pending` | Initiate Contact | `400 Bad Request` ("No collector assigned") |
| Citizen Owner | `completed` / `cancelled` | Initiate Contact | `400 Bad Request` ("Contact no longer active") |
| Other Citizen | Any | Initiate Contact | `403 Forbidden` |
| Unassigned Collector | Any | Initiate Contact | `403 Forbidden` |
| Unverified User | Any | Initiate Contact | `403 Forbidden` ("Email verification required") |
| Unauthenticated | Any | Initiate Contact | `401 Unauthorized` |

## 7. Provider Abstraction
The system uses an abstract base class `MaskedCommunicationProvider` located in `app/services/communication.py`:

```python
class MaskedCommunicationProvider(abc.ABC):
    @abc.abstractmethod
    def initiate_contact(
        self, pickup_request: PickupRequest, requester: User, recipient: User | None
    ) -> ContactSessionRead:
        pass
```

### Supported Provider Types
1. `MockMaskedCommunicationProvider` (`COMMUNICATION_PROVIDER=mock`)
2. `TwilioMaskedCommunicationProvider` (`COMMUNICATION_PROVIDER=twilio`)
3. `DisabledMaskedCommunicationProvider` (`COMMUNICATION_PROVIDER=disabled`)

## 8. Development / Mock Behavior
- **Default**: `COMMUNICATION_PROVIDER=mock`
- Does **NOT** execute real telephony, voice, or SMS calls.
- Returns synthetic virtual proxy session numbers (e.g. `+1-800-555-0199 (Ext #{id})`).
- Does **NOT** record or log real phone numbers or tokens.
- Clearly marked in UI and logs as mock development behavior.

## 9. Production Provider Requirements
For production deployment with real masked telephony:
1. Provision a telephony provider account (e.g., Twilio Proxy / Masked Phone Service).
2. Configure environment variables:
   - `COMMUNICATION_PROVIDER=twilio` (or provider name)
   - `COMMUNICATION_PROVIDER_API_KEY=<key>`
   - `COMMUNICATION_PROVIDER_SERVICE_SID=<sid>`
3. Complete `TwilioMaskedCommunicationProvider.initiate_contact()` implementation using official SDK/HTTP client.
4. Ensure provider callback webhooks (if used for call routing) validate signature headers.

## 10. Data Privacy Rules
- `citizen_phone` is redacted (`null`) in API responses for all collectors (including assigned collectors).
- `collector_phone` (if added in future schemas) is never returned to citizens.
- `ContactSessionRead` contains only proxy details, instructions, session ID, and expiration timestamp.
- Neither participant receives raw phone numbers or credentials.

## 11. Audit / Logging Behavior
When a contact session is initiated:
- Action: `communication_requested`
- Resource: `pickup_request`
- Resource ID: `<pickup_id>`
- After snapshot: `{"session_id": "...", "requester_role": "...", "status": "..."}`
- `SENSITIVE_KEYS` explicitly filters out `phone`, `citizen_phone`, `collector_phone`, `masked_phone`, `provider_secret`, `provider_token`, and `api_key`.

## 12. Testing
Backend test coverage in `tests/test_masked_communication.py` and `tests/test_security_boundaries.py`:
- Authorization checks for citizens, assigned collectors, unassigned collectors, cross-citizens, admins, and unverified users.
- Lifecycle scoping tests for `pending`, `accepted`, `on_the_way`, `completed`, and `cancelled` pickups.
- PII non-disclosure assertions verifying raw phone numbers are not in responses or logs.
- Provider fallback tests when service is disabled.

Frontend tests in `src/test/`:
- `MaskedContactModal` rendering, privacy notices, loading/error states, and session display.

## 13. Known Limitations
- Development mock mode produces static synthetic numbers for manual testing.
- Production telephony requires active Twilio/provider account credentials.

## 14. Deployment / Configuration Requirements
Environment variables in `.env` or deployment settings:
```env
COMMUNICATION_PROVIDER=mock
COMMUNICATION_PROVIDER_API_KEY=
COMMUNICATION_PROVIDER_SERVICE_SID=
```
