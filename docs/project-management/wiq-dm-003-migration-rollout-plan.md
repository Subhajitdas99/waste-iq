# WIQ-DM-003 Migration Strategy and Rollout Plan

## Objective

Move Waste-IQ from free-text, unpriced pickup data to a dealer-pilot-ready inventory model without disrupting live operations.

## Migration Strategy

## Phase 1: Add New Structures

Create without removing old behavior:

- `material_categories`
- `material_pricing_rules`
- `inventory_lots`
- `inventory_lot_events`
- `pickup_requests.material_category_id`
- `pickup_requests.material_description`

Keep `pickup_requests.waste_type` during transition.

## Phase 2: Seed Kolkata Pilot Taxonomy

Seed the initial Kolkata pilot category set:

- PET Bottles
- Mixed Plastic
- Cardboard
- Mixed Paper
- Ferrous Metal
- Non-Ferrous Metal
- Small E-Waste

## Phase 3: Backfill Existing Pickup Requests

Map current `waste_type` values into normalized categories.

### Recommended Mapping Approach

- deterministic mapping for clearly known strings
- manual review bucket for ambiguous historical values
- populate `material_description` with original free-text where useful

### Safety Rule

Do not block rollout on perfect historical cleanup.

Only new inventory creation must require normalized categories.

## Phase 4: Seed Initial Pricing Rules

Seed one active Kolkata pricing rule per pilot category.

### Required Pre-Launch Step

Business owner must approve the starting Kolkata rates before dealer browse goes live.

## Phase 5: Switch New Writes

Update all new pickup request and inventory flows to use:

- `material_category_id`
- optional `material_description`

Treat `waste_type` as legacy compatibility only.

## Phase 6: Enable Inventory Lot Creation

After categories and pricing are present:

- allow admin eligible-pickup listing
- allow priced lot creation
- start writing inventory audit events

## Phase 7: Enable Dealer Browse

Only after:

- approved dealers exist
- at least one active pricing rule exists
- at least one quality-reviewed lot exists

## Rollout Plan

## Step 1: Deploy Schema and Seed Data

Deploy database migration first.

Includes:

- taxonomy tables
- pricing tables
- inventory tables
- audit tables
- pilot category seed

## Step 2: Deploy Admin-Only Controls

Release admin pricing and inventory management before dealer browse.

Reason:

- lets operations validate taxonomy mapping and price accuracy internally

## Step 3: Dry Run in Staging

Run one complete scenario:

1. completed pickup exists
2. pickup has normalized category
3. active Kolkata pricing rule exists
4. admin creates priced lot
5. audit event is written
6. approved dealer can browse the lot

## Step 4: Internal Pilot Soft Launch

Enable only selected internal operators and one approved dealer account.

Reason:

- catches pricing or visibility issues before broader pilot exposure

## Step 5: First Real Dealer Pilot in Kolkata

Pilot conditions:

- limited approved dealer set
- limited material category set
- manually reviewed lots only
- no auto-listing

## Operational Guardrails

- no lot creation if no active pricing rule exists
- no dealer browse for unapproved dealers
- no archived or non-available lots shown to dealers
- no citizen PII exposed in dealer responses

## Rollback Strategy

If dealer browse must be paused:

- disable dealer inventory UI and API access
- keep admin pricing and inventory data intact
- preserve all created lots and audit events

If pricing rules are wrong:

- deactivate incorrect rule
- create corrected active rule
- do not mutate existing lot snapshots

## Launch Readiness Checklist

- taxonomy seed approved
- Kolkata pricing approved
- at least one completed pickup backfilled with normalized category
- at least one priced inventory lot created successfully
- dealer browse pagination verified
- audit trail visible for create and status change events
- dealer browse data privacy checked
