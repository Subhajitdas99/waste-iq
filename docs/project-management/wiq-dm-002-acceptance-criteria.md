# WIQ-DM-002 Acceptance Criteria

## Scope Lock

Only dealer profile and verification are included.

Explicitly out of scope:

- dealer marketplace browsing
- dealer reservation flow
- dealer pricing
- dealer transaction history

## Functional Acceptance Criteria

### AC-1 Dealer Profile Creation

- A user with role `dealer` can create exactly one dealer profile.
- The profile stores:
  - business name
  - owner name
  - phone
  - address
  - city
  - pincode
  - optional GST number
  - optional license number
  - accepted materials
  - verification status

### AC-2 Dealer Profile Retrieval and Update

- A dealer can fetch the current profile after creation.
- A dealer can update the profile.
- Updating an approved or rejected profile returns it to `pending` review.

### AC-3 Verification Workflow

- Every newly created dealer profile starts in `pending`.
- An admin can approve a dealer profile.
- An admin can reject a dealer profile.
- Approval stores an approval timestamp.
- Rejection clears any prior approval timestamp.

### AC-4 Admin Dealer Listing

- An admin can list dealer accounts and view:
  - account identity
  - profile completion
  - verification status
  - approval date

### AC-5 Dealer Dashboard Visibility

- The dealer dashboard displays:
  - profile completion
  - verification status
  - approval date
- If the dealer has no profile yet, the dashboard clearly prompts profile submission.

### AC-6 Role Protection

- Non-dealer users cannot access dealer profile endpoints.
- Non-admin users cannot approve, reject, or list dealers.
- Existing citizen, collector, and admin workflows remain unchanged.

## Non-Functional Acceptance Criteria

- Alembic migration creates the `dealer_profiles` table successfully.
- SQLite local development and PostgreSQL production both support the new schema.
- Frontend handles missing profile (`404`) gracefully for dealer users.
- Error states are surfaced cleanly for profile save and verification actions.
