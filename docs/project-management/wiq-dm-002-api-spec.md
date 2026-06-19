# WIQ-DM-002 API Specification

## Scope Boundary

This specification covers only dealer profile submission and admin verification.

Explicitly excluded:

- dealer marketplace listings
- dealer orders
- pricing
- lot reservation
- dealer verification automation beyond admin approve/reject

## Data Model

### Dealer Profile

- `business_name`
- `owner_name`
- `phone`
- `address`
- `city`
- `pincode`
- `gst_number` nullable
- `license_number` nullable
- `materials_accepted`
- `verification_status`
- `approved_at` nullable
- `created_at`
- `updated_at`

### Verification Status Values

- `pending`
- `approved`
- `rejected`

## Dealer APIs

### `POST /dealer/profile`

Create the authenticated dealer's business profile.

#### Request Body

```json
{
  "business_name": "Green Metal Traders",
  "owner_name": "Ravi Shaw",
  "phone": "9876543210",
  "address": "12 Canal Road, Kolkata",
  "city": "Kolkata",
  "pincode": "700001",
  "gst_number": "19ABCDE1234F1Z5",
  "license_number": "WB-SCRAP-221",
  "materials_accepted": ["Plastic", "Paper", "Cardboard"]
}
```

#### Success Response

`201 Created`

```json
{
  "id": 1,
  "user_id": 12,
  "business_name": "Green Metal Traders",
  "owner_name": "Ravi Shaw",
  "phone": "9876543210",
  "address": "12 Canal Road, Kolkata",
  "city": "Kolkata",
  "pincode": "700001",
  "gst_number": "19ABCDE1234F1Z5",
  "license_number": "WB-SCRAP-221",
  "materials_accepted": ["Plastic", "Paper", "Cardboard"],
  "verification_status": "pending",
  "approved_at": null,
  "created_at": "2026-06-19T10:30:00Z",
  "updated_at": "2026-06-19T10:30:00Z",
  "profile_completion": 100
}
```

### `GET /dealer/profile`

Return the authenticated dealer's profile and verification state.

#### Success Response

`200 OK`

Same schema as `POST /dealer/profile`.

#### Failure Modes

- `404 Not Found` when the dealer has not created a profile yet
- `403 Forbidden` for non-dealer roles

### `PATCH /dealer/profile`

Update the authenticated dealer's profile.

#### Request Body

Any subset of:

```json
{
  "business_name": "Updated Green Metal Traders",
  "city": "Howrah",
  "materials_accepted": ["Plastic", "E-waste"]
}
```

#### Business Rule

If an approved or rejected profile is edited, the profile automatically returns to `pending` review and `approved_at` is cleared.

#### Success Response

`200 OK`

Same schema as `GET /dealer/profile`.

## Admin Verification APIs

### `GET /admin/dealers`

List dealer accounts and current profile verification state.

#### Success Response

`200 OK`

```json
[
  {
    "user_id": 12,
    "user_name": "Ravi Shaw",
    "user_email": "ravi@example.com",
    "account_phone": "9876543210",
    "has_profile": true,
    "business_name": "Green Metal Traders",
    "owner_name": "Ravi Shaw",
    "city": "Kolkata",
    "pincode": "700001",
    "materials_accepted": ["Plastic", "Paper"],
    "verification_status": "pending",
    "approved_at": null,
    "profile_completion": 100,
    "created_at": "2026-06-19T10:30:00Z"
  }
]
```

### `POST /admin/dealers/{dealer_user_id}/approve`

Approve a dealer profile.

#### Success Response

`200 OK`

```json
{
  "user_id": 12,
  "verification_status": "approved",
  "approved_at": "2026-06-19T12:00:00Z"
}
```

### `POST /admin/dealers/{dealer_user_id}/reject`

Reject a dealer profile.

#### Success Response

`200 OK`

```json
{
  "user_id": 12,
  "verification_status": "rejected",
  "approved_at": null
}
```

## Error Handling

- `400 Bad Request`
  - dealer profile already exists
  - materials accepted is empty
- `401 Unauthorized`
  - missing or invalid bearer token
- `403 Forbidden`
  - non-dealer accessing dealer profile APIs
  - non-admin accessing admin dealer verification APIs
- `404 Not Found`
  - dealer profile not found for `GET`, `PATCH`, `approve`, or `reject`
