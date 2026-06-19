# WIQ-DM-003 Database Schema

## Goal

Support a priced, auditable inventory layer for the first real dealer pilot in Kolkata.

## Schema Changes

## 1. `pickup_requests`

### Existing Problem

The table currently uses free-text `waste_type`.

### New Columns

- `material_category_id` nullable during migration, later required for new writes
- `material_description` nullable

### Legacy Column

- keep `waste_type` temporarily for compatibility and backfill

## 2. `material_categories`

### Purpose

Normalized taxonomy table.

### Columns

- `id` primary key
- `code` unique
- `name`
- `description` nullable
- `is_active`
- `display_order`
- `created_at`
- `updated_at`

### Seed Set for Kolkata Pilot

- PET Bottles
- Mixed Plastic
- Cardboard
- Mixed Paper
- Ferrous Metal
- Non-Ferrous Metal
- Small E-Waste

## 3. `material_pricing_rules`

### Purpose

Admin-managed per-kg pricing table.

### Columns

- `id` primary key
- `material_category_id` foreign key
- `city`
- `unit_price_per_kg`
- `currency_code`
- `is_active`
- `effective_from`
- `effective_to` nullable
- `created_by` foreign key to `users`
- `updated_by` foreign key to `users`
- `created_at`
- `updated_at`

### Constraints

- one active rule per material category and city

## 4. `inventory_lots`

### Purpose

Dealer-browseable inventory linked to completed pickups.

### Columns

- `id` primary key
- `pickup_request_id` foreign key, unique
- `citizen_id` foreign key to `users`
- `collector_id` foreign key to `users`
- `material_category_id` foreign key
- `material_description` nullable
- `weight_kg`
- `unit_price_per_kg_snapshot`
- `total_listed_amount`
- `pricing_rule_id` nullable foreign key
- `source_city`
- `status`
- `archived_at` nullable
- `created_by` foreign key to `users`
- `updated_by` foreign key to `users`
- `created_at`
- `updated_at`

### Status Enum

- `available`
- `reserved`
- `sold`

### Constraints

- unique lot per pickup request
- positive weight
- immutable snapshot pricing after creation

## 5. `inventory_lot_events`

### Purpose

Audit log for lot lifecycle activity.

### Columns

- `id` primary key
- `inventory_lot_id` foreign key
- `event_type`
- `previous_status` nullable
- `new_status` nullable
- `actor_user_id` foreign key to `users`
- `event_notes` nullable
- `metadata_json` nullable
- `created_at`

## Recommended Indexes

- `pickup_requests.material_category_id`
- `material_categories.code`
- `material_pricing_rules(material_category_id, city)`
- `material_pricing_rules.is_active`
- `inventory_lots.pickup_request_id` unique
- `inventory_lots.material_category_id`
- `inventory_lots.source_city`
- `inventory_lots.status`
- `inventory_lots.archived_at`
- `inventory_lot_events.inventory_lot_id`
- `inventory_lot_events.created_at`
