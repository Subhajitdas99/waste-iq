# WIQ-DM-003 API Specification

## Scope Boundary

This specification covers:

- material taxonomy lookup
- admin pricing CRUD
- admin inventory creation and management
- inventory audit visibility
- approved dealer browse-only inventory access

Explicitly excluded:

- dealer order creation
- checkout
- payment tracking
- AI features

## API Design Principles

- normalized categories replace free-text category selection
- pricing is rule-driven but lots store immutable snapshots
- dealer inventory APIs are read-only
- dealer inventory listing requires pagination
- dealer inventory access is allowed only for approved dealers

## Material Taxonomy APIs

### `GET /material-categories`

Return active material categories for product forms and filters.

#### Success Response

`200 OK`

```json
[
  {
    "id": 1,
    "code": "pet_bottles",
    "name": "PET Bottles",
    "description": "Clean or mixed PET bottle loads",
    "display_order": 1
  }
]
```

### `GET /admin/material-categories`

Return all material categories for admin review.

Recommended MVP note:

- category creation can be seed-driven in the first Kolkata release
- this endpoint may be read-only if admin taxonomy CRUD is deferred

## Admin Pricing APIs

### `GET /admin/material-pricing`

List pricing rules.

#### Query Parameters

- `material_category_id` optional
- `city` optional
- `is_active` optional

#### Success Response

`200 OK`

```json
[
  {
    "id": 11,
    "material_category_id": 1,
    "material_category_name": "PET Bottles",
    "city": "Kolkata",
    "unit_price_per_kg": 24.5,
    "currency_code": "INR",
    "is_active": true,
    "effective_from": "2026-06-20T00:00:00Z",
    "effective_to": null,
    "created_at": "2026-06-19T09:00:00Z",
    "updated_at": "2026-06-19T09:00:00Z"
  }
]
```

### `POST /admin/material-pricing`

Create a pricing rule.

#### Request Body

```json
{
  "material_category_id": 1,
  "city": "Kolkata",
  "unit_price_per_kg": 24.5,
  "currency_code": "INR",
  "is_active": true,
  "effective_from": "2026-06-20T00:00:00Z"
}
```

#### Business Rules

- city is required for WIQ-DM-003 pilot pricing
- only one active rule per `material_category_id + city`
- if a new active rule is created, prior active rule must be deactivated in a controlled way

### `PATCH /admin/material-pricing/{pricing_rule_id}`

Update a pricing rule.

#### Editable Fields

- `unit_price_per_kg`
- `is_active`
- `effective_from`
- `effective_to`

#### Success Response

`200 OK`

Same schema as `GET /admin/material-pricing`.

### `POST /admin/material-pricing/{pricing_rule_id}/activate`

Activate a pricing rule and deactivate any conflicting active rule for the same category and city.

### `POST /admin/material-pricing/{pricing_rule_id}/deactivate`

Deactivate a pricing rule.

## Admin Inventory APIs

### `GET /admin/inventory-lots/eligible-pickups`

List completed pickup requests eligible for lot creation.

#### Eligibility Rules

- pickup status is `completed`
- assignment has non-null positive `weight_kg`
- no existing inventory lot for the pickup request

#### Success Response

`200 OK`

```json
[
  {
    "pickup_request_id": 82,
    "citizen_id": 11,
    "collector_id": 5,
    "material_category_id": 2,
    "material_category_name": "Mixed Plastic",
    "material_description": "Household plastic containers and packaging",
    "weight_kg": 18.5,
    "source_city": "Kolkata",
    "completed_at": "2026-06-19T13:45:00Z"
  }
]
```

### `POST /admin/inventory-lots`

Create a priced inventory lot from one eligible pickup.

#### Request Body

```json
{
  "pickup_request_id": 82,
  "material_category_id": 2,
  "material_description": "Household plastic containers and packaging",
  "status": "available"
}
```

#### Business Rules

- `pickup_request_id` must be eligible
- system derives `weight_kg` from collector-completed pickup
- system resolves active pricing rule by `material_category_id + source_city`
- system stores:
  - `unit_price_per_kg_snapshot`
  - `total_listed_amount`
- only one lot may exist per pickup request

#### Success Response

`201 Created`

```json
{
  "id": 14,
  "pickup_request_id": 82,
  "material_category_id": 2,
  "material_category_name": "Mixed Plastic",
  "material_description": "Household plastic containers and packaging",
  "weight_kg": 18.5,
  "unit_price_per_kg_snapshot": 24.5,
  "total_listed_amount": 453.25,
  "source_city": "Kolkata",
  "status": "available",
  "archived_at": null,
  "created_at": "2026-06-19T14:00:00Z",
  "updated_at": "2026-06-19T14:00:00Z"
}
```

### `GET /admin/inventory-lots`

List inventory lots for internal operators.

#### Query Parameters

- `status` optional
- `city` optional
- `material_category_id` optional
- `archived` optional boolean

### `GET /admin/inventory-lots/{lot_id}`

Return one inventory lot with internal details.

### `PATCH /admin/inventory-lots/{lot_id}`

Update admin-managed lot fields.

#### Editable Fields

- `material_description`
- `status`
- `archived_at` not directly editable via generic patch

Recommended optional field:

- `material_category_id`

Only allow category change if:

- lot is not archived
- status is not `sold`
- system recalculates snapshot values using the active pricing rule for the new category
- audit event is written

### `POST /admin/inventory-lots/{lot_id}/archive`

Archive a lot.

#### Success Response

`200 OK`

```json
{
  "id": 14,
  "status": "available",
  "archived_at": "2026-06-19T16:00:00Z"
}
```

### `GET /admin/inventory-lots/{lot_id}/events`

Return the lot audit trail.

#### Success Response

`200 OK`

```json
[
  {
    "id": 301,
    "event_type": "created",
    "previous_status": null,
    "new_status": "available",
    "actor_user_id": 1,
    "event_notes": "Lot created from completed pickup.",
    "created_at": "2026-06-19T14:00:00Z"
  }
]
```

## Dealer Inventory APIs

### Access Rule

Dealer browse requires:

- authenticated `dealer` role
- existing dealer profile
- `verification_status = approved`

Pending or rejected dealers receive `403 Forbidden`.

### `GET /dealer/inventory-lots`

Return browseable inventory for approved dealers.

#### Visibility Rules

Return only lots where:

- `status = available`
- `archived_at IS NULL`

#### Query Parameters

- `material_category_id` optional
- `city` optional
- `page` required, default `1`
- `page_size` required, default `20`, max recommended `50`

#### Success Response

`200 OK`

```json
{
  "items": [
    {
      "id": 14,
      "material_category_id": 2,
      "material_category_name": "Mixed Plastic",
      "material_description": "Household plastic containers and packaging",
      "weight_kg": 18.5,
      "unit_price_per_kg_snapshot": 24.5,
      "total_listed_amount": 453.25,
      "source_city": "Kolkata",
      "status": "available",
      "created_at": "2026-06-19T14:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total_items": 1,
  "total_pages": 1
}
```

### `GET /dealer/inventory-lots/{lot_id}`

Return one browseable lot.

#### Visibility Rules

- lot must be `available`
- lot must not be archived

#### Dealer Response Fields

Must include:

- category
- optional description
- weight
- price per kg
- total listed amount
- city

Must exclude:

- citizen identity
- full address
- collector identity
- admin notes
- internal actor IDs

## Error Handling

- `400 Bad Request`
  - pickup is not eligible
  - no active pricing rule exists for selected category and city
  - conflicting active pricing rule creation
  - duplicate lot creation
- `401 Unauthorized`
  - missing or invalid bearer token
- `403 Forbidden`
  - non-admin accessing admin APIs
  - non-dealer accessing dealer APIs
  - dealer not approved for browse access
- `404 Not Found`
  - lot not found
  - pricing rule not found
  - dealer requested non-browseable lot

## API Notes

- lots must never reprice automatically after creation
- dealer APIs are read-only in WIQ-DM-003
- audit events should be emitted for create, update, status change, and archive
