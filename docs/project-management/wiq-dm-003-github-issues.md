# WIQ-DM-003 GitHub Issues

## Epic

WIQ-DM-003 Inventory, Pricing, Material Taxonomy, and Audit Trail

## Goal

Make Waste-IQ inventory dealer-pilot ready in Kolkata by adding:

- normalized material categories
- admin pricing rules
- priced inventory lots
- inventory audit events
- approved dealer browse access with pagination

## Issue 1: Add material taxonomy foundation and pickup request normalization

### Purpose

Replace free-text waste categories with normalized material categories.

### Scope

- create `material_categories` table
- seed Kolkata pilot category set
- add `material_category_id` and `material_description` to pickup requests
- preserve legacy `waste_type` temporarily for migration compatibility
- add category lookup API

### Acceptance Criteria

- new normalized categories exist in the database
- pickup requests can reference a normalized category
- optional description is supported
- legacy free-text category is no longer the primary source of truth

## Issue 2: Add pricing foundation and admin pricing CRUD

### Purpose

Ensure all pilot inventory can carry a real listed price.

### Scope

- create `material_pricing_rules` table
- support city-scoped Kolkata pricing
- add admin pricing CRUD
- support active pricing rule behavior

### Acceptance Criteria

- admin can create, edit, activate, and deactivate pricing rules
- only one active pricing rule exists per category-city pair
- pricing rules are queryable for admin review

## Issue 3: Add InventoryLot model with immutable pricing snapshot

### Purpose

Create the dealer-facing inventory entity backed by completed pickups.

### Scope

- create `inventory_lots` table
- link each lot to one completed pickup
- store `material_category_id`
- store `weight_kg`
- store `unit_price_per_kg_snapshot`
- store `total_listed_amount`
- support `available`, `reserved`, `sold`
- support `archived_at`
- track `created_by` and `updated_by`

### Acceptance Criteria

- one completed pickup creates at most one lot
- lot stores immutable price snapshot data
- archived lots retain their original marketplace status

## Issue 4: Add inventory audit trail

### Purpose

Make pilot inventory operationally traceable.

### Scope

- create `inventory_lot_events` table
- log lot creation
- log lot updates
- log status changes
- log archive actions

### Acceptance Criteria

- every lot create, update, status change, and archive action emits an event
- each event records actor and timestamp

## Issue 5: Build admin eligible-pickup and lot creation workflow

### Purpose

Allow admins to convert completed pickups into priced inventory.

### Scope

- define eligible pickup query
- enforce completed status and final weight rules
- resolve active pricing rule during lot creation
- block lot creation when no active pricing exists

### Acceptance Criteria

- admin can list eligible completed pickups
- admin can create a lot only when a valid active pricing rule exists
- duplicate lot creation is blocked

## Issue 6: Build admin inventory management and audit APIs

### Purpose

Give operators full control over inventory visibility and audit review.

### Scope

- list lots
- lot detail
- edit lot metadata
- status change
- archive action
- lot event history API

### Acceptance Criteria

- admin can manage inventory without database intervention
- admin can inspect lot audit history
- admin can filter lots by category, city, status, and archive state

## Issue 7: Build dealer browse-only inventory APIs with pagination

### Purpose

Expose priced available inventory to approved dealers.

### Scope

- list available lots
- pagination
- filter by category
- filter by city
- lot detail endpoint
- dealer approval gating

### Acceptance Criteria

- only approved dealers can browse inventory
- dealer list is paginated
- dealer sees category, weight, price per kg, and total listed amount
- dealer never sees citizen PII or internal notes

## Issue 8: Add admin pricing and inventory dashboard

### Purpose

Provide a single internal workflow for pricing and lot management.

### Scope

- pricing management section
- eligible pickup section
- lot creation action
- inventory list
- status update UI
- archive UI
- audit timeline preview

### Acceptance Criteria

- admin can manage pricing and inventory in-product
- admin can see active inventory counts and audit visibility

## Issue 9: Add dealer inventory browsing dashboard

### Purpose

Provide the first real dealer pilot browse experience.

### Scope

- paginated lot list
- category and city filters
- price display
- lot detail preview
- verification lock messaging

### Acceptance Criteria

- approved dealers can browse available inventory
- pending and rejected dealers are blocked with clear messaging
- dealer UI is browse-only

## Issue 10: Add migration, QA, and Kolkata pilot dry run

### Purpose

Prepare the release for the first real dealer pilot.

### Scope

- legacy waste-type mapping plan
- pricing seed validation
- migration verification
- end-to-end staging walkthrough
- pilot readiness checklist

### Acceptance Criteria

- team can demonstrate one completed Kolkata pickup becoming one priced dealer-visible lot
- no existing dealer verification or pickup workflow regresses

## Recommended Build Order

1. Issue 1: Material taxonomy foundation
2. Issue 2: Pricing foundation
3. Issue 3: InventoryLot model with snapshot pricing
4. Issue 4: Inventory audit trail
5. Issue 5: Admin eligible-pickup and lot creation workflow
6. Issue 6: Admin inventory management and audit APIs
7. Issue 7: Dealer browse-only inventory APIs with pagination
8. Issue 8: Admin pricing and inventory dashboard
9. Issue 9: Dealer inventory browsing dashboard
10. Issue 10: Migration, QA, and Kolkata pilot dry run
