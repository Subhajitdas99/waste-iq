# WIQ-DM-003 Technical Specification

## Title

WIQ-DM-003 Inventory, Pricing, Material Taxonomy, and Audit Trail

## Objective

Update WIQ-DM-003 so Waste-IQ is ready for the first real dealer pilot in Kolkata.

The milestone must transform completed pickups into dealer-browseable inventory with:

- normalized material categories
- admin-managed pricing rules
- immutable pricing snapshots on lots
- inventory auditability

## Product Goal

Enable Waste-IQ to present real, priced inventory to approved dealers in Kolkata without yet introducing orders, checkout, or payment flows.

## Scope Boundary

Included in scope:

- `InventoryLot` model
- material taxonomy normalization
- pricing foundation
- immutable price snapshot on lots
- inventory audit trail
- admin inventory management
- dealer inventory browsing with pagination and filters

Explicitly out of scope:

- dealer order creation
- dealer checkout
- payment gateway
- AI classification
- AI pricing
- GPS logistics
- municipality reporting changes

## Why Scope Changed

Inventory alone is not enough for a dealer pilot.

For a real Kolkata pilot, dealers need:

- a clear material category they recognize
- a visible per-kg price
- a total listed value
- confidence that inventory changes are traceable

Without those elements, the product remains an internal operations tool rather than a dealer-ready marketplace surface.

## Current Repository Baseline

The repository already supports:

- dealer role
- dealer profile creation
- admin dealer approval and rejection
- completed pickup lifecycle
- collector-reported final weight
- admin and dealer dashboards

The repository still uses free-text `waste_type` on pickup requests and has no pricing or inventory lot model yet.

## Pilot Strategy

The first real dealer pilot should optimize for controlled supply exposure in Kolkata.

Recommended operating model:

1. collector completes a pickup with final weight
2. admin reviews eligibility and material classification
3. system applies the currently active Kolkata pricing rule for that material
4. admin creates the inventory lot
5. approved dealers browse only `available` Kolkata-ready inventory

## Key Product Decisions

### Decision 1: Admin-created lots, not automatic lots

For the Kolkata pilot, lot creation should remain admin initiated.

Reason:

- material quality can be reviewed before dealer exposure
- category normalization can be corrected during early pilot operations
- pricing mistakes are caught before lots go live

### Decision 2: Pricing is rule-based, but lots store immutable snapshots

Pricing rules can change over time, but once a lot is created, its snapshot values must not change automatically.

Immutable lot snapshot fields:

- `unit_price_per_kg_snapshot`
- `total_listed_amount`

Optional traceability field:

- `pricing_rule_id` nullable reference retained for audit

### Decision 3: Statuses remain simple

Marketplace lot statuses remain:

- `available`
- `reserved`
- `sold`

Archive is not a status value.

Archive should be modeled via:

- `archived_at`

### Decision 4: Material taxonomy replaces free-text categories

Pickup requests and inventory lots should use normalized material categories.

Free text remains allowed only as an optional human description, not as the primary category source.

### Decision 5: Approved dealers only

Inventory browsing must remain restricted to dealers whose verification status is `approved`.

### Decision 6: Pagination is mandatory

Dealer inventory browsing must support pagination from the first release.

Reason:

- dealer lists will grow
- page performance must stay predictable
- pilot inventory feeds must not become unbounded

## Functional Scope

## 1. Material Taxonomy

### Goal

Replace free-text waste categories with normalized categories suitable for pricing, filtering, and future transaction flows.

### Requirements

- material category is selected from a normalized set
- optional free-text material description remains available
- category becomes the system source of truth

### Recommended Kolkata Pilot Taxonomy

Start with a deliberately small set of categories:

- `pet_bottles`
- `mixed_plastic`
- `cardboard`
- `mixed_paper`
- `ferrous_metal`
- `non_ferrous_metal`
- `small_ewaste`

Reason:

- enough breadth for early dealer conversations
- limited enough for pricing discipline
- easier for admin review during pilot

## 2. Pricing Foundation

### Goal

Create a reliable way to attach active pricing to pilot inventory.

### Requirements

- pricing table by material category
- Kolkata city scope in MVP
- admin pricing CRUD
- active pricing rules
- immutable price snapshot on inventory lots

### Active Rule Semantics

Recommended MVP rule:

- one active pricing rule per `material_category_id` and `city` at a time

### Pricing Behavior on Lot Creation

When admin creates a lot:

1. system finds the active pricing rule for the lot's material category and city
2. system copies the current rule into immutable lot snapshot fields
3. later pricing changes do not mutate previously listed lots

## 3. Inventory Lots

### Goal

Represent dealer-facing supply derived from completed pickups.

### Requirements

- link lot to completed pickup request
- store normalized material category
- store final weight
- store pricing snapshot
- store total listed value
- support `available`, `reserved`, `sold`
- support archive behavior via `archived_at`

## 4. Inventory Audit Trail

### Goal

Make lot lifecycle changes traceable for pilot operations.

### Requirements

- inventory lot events table
- created-by tracking
- updated-by tracking
- status change tracking
- actor traceability for admin actions

## Updated Domain Model

## MaterialCategory

### Purpose

Provide the normalized category system used by pickup requests, pricing, and inventory.

### Core Fields

- `id`
- `code`
- `name`
- `description`
- `is_active`
- `display_order`
- `created_at`
- `updated_at`

## MaterialPricingRule

### Purpose

Store admin-managed per-kg pricing used to list lots.

### Core Fields

- `id`
- `material_category_id`
- `city`
- `unit_price_per_kg`
- `currency_code`
- `is_active`
- `effective_from`
- `effective_to` nullable
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

## InventoryLot

### Purpose

Represent a priced, browseable material lot linked to a completed pickup request.

### Core Fields

- `id`
- `pickup_request_id`
- `citizen_id`
- `collector_id`
- `material_category_id`
- `material_description` nullable
- `weight_kg`
- `unit_price_per_kg_snapshot`
- `total_listed_amount`
- `pricing_rule_id` nullable
- `source_city`
- `status`
- `archived_at` nullable
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

## InventoryLotEvent

### Purpose

Provide an internal audit trail of lot lifecycle changes.

### Core Fields

- `id`
- `inventory_lot_id`
- `event_type`
- `previous_status` nullable
- `new_status` nullable
- `actor_user_id`
- `event_notes` nullable
- `metadata_json` nullable
- `created_at`

## Updated Database Schema

## Pickup Request Changes

The current `pickup_requests` table uses free-text `waste_type`.

### New Fields

- `material_category_id` nullable during migration, required for new records after rollout
- `material_description` nullable

### Legacy Field Handling

- keep existing `waste_type` temporarily for migration compatibility
- stop using `waste_type` as the primary source of truth after rollout
- plan later cleanup migration once all clients have switched

## New Table: `material_categories`

### Required Fields

- `id`
- `code` unique
- `name`
- `description` nullable
- `is_active`
- `display_order`
- `created_at`
- `updated_at`

## New Table: `material_pricing_rules`

### Required Fields

- `id`
- `material_category_id`
- `city`
- `unit_price_per_kg`
- `currency_code`
- `is_active`
- `effective_from`
- `effective_to` nullable
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

### Integrity Rules

- only one active rule per `material_category_id + city`
- historical rules remain stored after deactivation

## New Table: `inventory_lots`

### Required Fields

- `id`
- `pickup_request_id` unique
- `citizen_id`
- `collector_id`
- `material_category_id`
- `material_description` nullable
- `weight_kg`
- `unit_price_per_kg_snapshot`
- `total_listed_amount`
- `pricing_rule_id` nullable
- `source_city`
- `status`
- `archived_at` nullable
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

### Integrity Rules

- one lot per pickup request
- pickup request must be completed
- `weight_kg > 0`
- `unit_price_per_kg_snapshot >= 0`
- `total_listed_amount = weight_kg * unit_price_per_kg_snapshot`

## New Table: `inventory_lot_events`

### Required Fields

- `id`
- `inventory_lot_id`
- `event_type`
- `previous_status` nullable
- `new_status` nullable
- `actor_user_id`
- `event_notes` nullable
- `metadata_json` nullable
- `created_at`

### Event Types

Recommended MVP event types:

- `created`
- `updated`
- `status_changed`
- `archived`

## Inventory Status Semantics

### `available`

- visible to approved dealers
- counted as active inventory

### `reserved`

- not visible in dealer browse
- used only by admin/internal operations in WIQ-DM-003

### `sold`

- not visible in dealer browse
- indicates commercially unavailable inventory

### Archive Behavior

- archived lots are excluded from dealer browse
- archived lots are hidden from default admin active views
- archive preserves original status

## Updated Admin Workflow

1. Admin maintains active Kolkata pricing rules by material category.
2. Admin reviews completed pickups eligible for listing.
3. Admin selects normalized material category.
4. Admin optionally records material description.
5. System applies the active pricing rule snapshot.
6. Admin creates the lot.
7. System writes an audit event.
8. Admin may later edit notes or status, and those changes are logged.

## Updated Dealer Workflow

1. Approved dealer signs in.
2. Dealer accesses inventory browsing dashboard.
3. Dealer sees paginated `available` inventory only.
4. Dealer filters by category and city.
5. Dealer views priced lot information for later offline deal conversation.

## Frontend Requirements

## Admin Inventory Management

Required sections:

- pricing management section
- category-aware completed pickups eligible for listing
- lot creation form
- inventory lot list
- lot detail/edit panel
- archive action
- audit timeline preview

Required lot fields in admin UI:

- pickup request ID
- category
- optional description
- weight
- unit price per kg
- total listed amount
- city
- status
- archived state
- created by / updated by

## Admin Pricing Management

Required sections:

- list pricing rules
- create pricing rule
- edit pricing rule
- activate and deactivate rule
- category and city visibility

## Dealer Inventory Browsing

Required sections:

- verification gate messaging
- paginated inventory list
- filters for category and city
- lot price per kg
- total listed amount
- lot detail preview

## Non-Functional Requirements

- no dealer-visible citizen PII
- immutable lot pricing snapshots
- consistent category and pricing behavior between admin and dealer APIs
- pagination required on dealer listing API
- audit events written for create, edit, status change, and archive actions

## Risks

### Risk 1: Category migration ambiguity

Existing free-text pickup data may not map cleanly to the new taxonomy.

Mitigation:

- seed a limited Kolkata pilot taxonomy
- use admin review during lot creation
- keep optional free-text description for edge cases

### Risk 2: Pricing rule conflicts

Multiple active rules for the same material and city could create inconsistent listings.

Mitigation:

- enforce a single active rule per category-city pair

### Risk 3: Dealer trust gap

Dealers may distrust lots if prices change after exposure.

Mitigation:

- store immutable price snapshots on lots

### Risk 4: Audit gaps

Operational disputes may occur if inventory edits are not traceable.

Mitigation:

- add inventory lot event logging from the first pilot release

## Definition of Done

WIQ-DM-003 is complete when:

1. admin can manage Kolkata pricing rules by material category
2. completed pickups can be converted into category-normalized lots
3. lot creation stores immutable price snapshots and total listed amount
4. inventory changes generate audit events
5. approved dealers can browse paginated available lots filtered by category and city
6. no order or payment flow has been introduced
