# WIQ-DM-003 Acceptance Criteria

## Scope Lock

WIQ-DM-003 includes:

- inventory lots
- pricing foundation
- material taxonomy
- inventory audit trail

Explicitly out of scope:

- dealer orders
- payment gateway
- AI features
- dealer checkout

## Functional Acceptance Criteria

### AC-1 Material Taxonomy

- Pickup requests support normalized `material_category_id`.
- Pickup requests allow optional `material_description`.
- Active category list is available for product forms and filters.
- Legacy free-text category is not used as the primary category source for new inventory flows.

### AC-2 Pricing Foundation

- Admin can create, edit, activate, and deactivate material pricing rules.
- Pricing rules are scoped by material category and city.
- The system prevents more than one active pricing rule per category-city pair.

### AC-3 Inventory Lot Creation

- Admin can create an inventory lot only from a completed pickup request with positive final weight.
- System applies the active pricing rule at creation time.
- Lot stores:
  - material category
  - optional description
  - final weight
  - immutable `unit_price_per_kg_snapshot`
  - immutable `total_listed_amount`
  - status
  - `archived_at`

### AC-4 Inventory Status and Archive

- Lots support exactly:
  - `available`
  - `reserved`
  - `sold`
- Admin can archive a lot without creating a fourth marketplace status.
- Archived lots do not appear in dealer browse results.

### AC-5 Inventory Audit Trail

- System records lot events for:
  - creation
  - update
  - status change
  - archive
- Each event records actor and timestamp.

### AC-6 Dealer Browse Access

- Only approved dealers can browse inventory.
- Pending and rejected dealers are blocked from inventory browse APIs and pages.
- Dealer inventory listing is paginated.
- Dealers can filter by category and city.

### AC-7 Dealer Data Shape

- Dealer browse responses include:
  - category
  - optional description
  - weight
  - unit price per kg
  - total listed amount
  - city
- Dealer browse responses exclude:
  - citizen identity
  - full address
  - collector identity
  - internal admin notes
  - internal audit fields

### AC-8 Admin Workflow Support

- Admin can view active and archived lots.
- Admin can identify eligible pickups for lot creation.
- Admin can manage pricing and inventory in the product UI.
- Admin can inspect lot audit history.

### AC-9 Existing Workflow Protection

- Existing auth, dealer verification, citizen dashboard, collector dashboard, admin dashboard, and pickup lifecycle continue to work.
- Completed pickup remains the eligibility gate for inventory creation.

## Non-Functional Acceptance Criteria

- Alembic migration creates new taxonomy, pricing, inventory, and audit tables successfully.
- Legacy pickup data can be mapped forward without blocking the release.
- Lot pricing does not mutate when pricing rules change later.
- Dealer inventory list performance remains predictable through pagination.
