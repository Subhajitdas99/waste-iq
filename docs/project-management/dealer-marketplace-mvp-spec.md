# Waste-IQ Dealer Marketplace MVP Specification

## Version

- Product version: v1.1.0
- Document status: Proposed
- Priority: Highest after launch hardening

## Objective

Build the Dealer Marketplace MVP before WhatsApp, GPS, or AI so Waste-IQ can:

1. onboard the first paying dealer
2. complete the first revenue-generating waste transaction
3. prove startup launch readiness with a controlled commercial workflow

## Executive Summary

Waste-IQ already supports the citizen to collector pickup lifecycle. The next commercial step is to convert completed pickups into dealer-purchasable inventory and record the resulting transaction value and platform commission.

The Dealer Marketplace MVP should not attempt a full exchange, auction system, or logistics network. It should focus on a narrow flow:

1. Citizen requests pickup
2. Collector completes pickup with actual weight
3. System or admin creates an available material lot
4. Verified dealer browses available lots
5. Dealer reserves or purchases a lot
6. Admin confirms fulfillment and settlement
7. Waste-IQ records revenue and transaction success

## Product Goal

Enable Waste-IQ to support one verified dealer purchasing collected recyclable waste through the platform with traceable inventory, transaction status, and platform revenue reporting.

## Why This MVP Matters

This is the shortest path from operations software to a monetizable marketplace.

Without a dealer workflow, Waste-IQ remains:

- a pickup management tool
- an analytics dashboard
- a pre-revenue operations platform

With a dealer workflow, Waste-IQ becomes:

- a supply aggregation platform
- a commercial transaction layer
- a stronger candidate for launch and pilot sales

## Non-Goals

The Dealer Marketplace MVP explicitly excludes:

- WhatsApp-based notifications
- GPS and live vehicle tracking
- AI waste classification
- AI price prediction
- recycler-specific workflows
- dealer bidding and auction systems
- automated payment gateway integration
- dynamic route optimization
- multi-warehouse inventory management
- municipality-specific reporting enhancements beyond current admin needs

## Current Platform Baseline

Based on v1.1.0, Waste-IQ currently has:

- citizen role
- collector role
- admin role
- pickup request lifecycle
- collector assignment
- request event timeline
- admin analytics

It does not yet have:

- dealer role
- business verification workflow
- inventory lots for collected material
- transaction states between supply and buyer
- platform commission reporting tied to dealer purchases

## MVP User Roles

## Citizen

Creates recyclable pickup requests.

### Responsibilities in MVP

- submit request
- provide waste type and address
- wait for collection

### Changes Required

- none required for dealer workflow beyond existing pickup flow

## Collector

Completes pickup and records actual collected weight.

### Responsibilities in MVP

- accept request
- mark collection stages
- enter actual collected weight

### Changes Required

- actual weight must be reliable enough to generate a sellable lot

## Dealer

New buyer-side role for the MVP.

### Responsibilities in MVP

- complete registration or be created by admin
- submit business profile
- wait for verification
- browse available lots
- reserve or purchase material

## Admin

Controls marketplace trust, pricing, and transaction oversight.

### Responsibilities in MVP

- verify dealers
- manage category pricing or default sell rates
- review listings and reservations
- confirm sale completion
- view transaction and revenue reporting

## Recommended MVP Workflow

## Phase 1: Supply Creation

1. Citizen creates pickup request.
2. Collector accepts and completes pickup.
3. Collector enters actual collected weight.
4. Platform marks request completed.
5. Platform creates an inventory lot from the completed pickup, or admin converts it into a lot.

## Phase 2: Dealer Purchase

1. Verified dealer signs in.
2. Dealer sees available inventory lots filtered by category, city, and quantity.
3. Dealer opens lot details.
4. Dealer reserves the lot or submits a purchase intent at the listed price.
5. Admin confirms the reservation and coordinates offline fulfillment if needed.

## Phase 3: Revenue Recognition

1. Admin marks the order as confirmed and fulfilled.
2. System stores sale amount, commission amount, and dealer linkage.
3. Admin dashboard reflects dealer transaction metrics.

## Recommended Commercial Model for MVP

To optimize for the first paying dealer, use a simple fixed-price model.

### Pricing Model

- Admin defines category-level default price per kilogram
- Inventory lot stores the applied unit price at listing time
- Dealer sees fixed price, not negotiable price

### Revenue Model

- Waste-IQ takes a flat commission percentage on the completed dealer transaction
- Commission is recorded in system even if settlement occurs offline

### Why This Model

- fastest to implement
- easiest to explain to first dealer
- avoids bid negotiation complexity
- makes revenue measurable from day one

## Functional Requirements

### FR-1 Dealer Role Support

The system must support a new `dealer` user role with dedicated access permissions.

### FR-2 Dealer Onboarding

Dealer accounts must include business profile data and remain inactive for marketplace purchase actions until approved by admin.

### FR-3 Dealer Verification

Admin must be able to review and approve or reject dealer access.

### FR-4 Inventory Lot Creation

Completed pickups must become marketplace inventory lots either automatically or through admin approval.

Recommended MVP behavior:

- auto-create lot when pickup status becomes completed and actual weight is present

### FR-5 Inventory Visibility

Verified dealers must be able to browse only lots that are available for purchase.

### FR-6 Lot Detail View

Dealers must be able to view lot details including category, weight, approximate location, listed price, and availability status.

### FR-7 Reservation or Purchase Intent

Dealers must be able to reserve an available lot or submit purchase intent once per lot.

Recommended MVP behavior:

- reserve lot at fixed price

### FR-8 Admin Order Oversight

Admin must be able to view dealer reservations, confirm sale status, and cancel invalid transactions.

### FR-9 Commercial Transaction Recording

When a dealer purchase is confirmed, the system must store:

- dealer identity
- lot identity
- weight
- unit price
- gross transaction value
- platform commission value
- order status history

### FR-10 Revenue Analytics

Admin analytics must show:

- available lots count
- reserved lots count
- sold lots count
- gross dealer transaction value
- platform commission revenue
- active verified dealers

## Database Changes Required

The current schema supports pickup requests, collector assignments, and users. Dealer Marketplace MVP requires new commercial entities and one role expansion.

## 1. User Role Expansion

### Existing

- `users.role` supports `citizen`, `collector`, `admin`

### Change

- add `dealer`

### Reason

- dedicated authenticated access for buyer-side workflows

## 2. Dealer Profile Table

### Table

`dealer_profiles`

### Purpose

Store business and verification information separate from the base `users` table.

### Required Fields

- `id`
- `user_id` unique foreign key to `users`
- `business_name`
- `contact_person_name`
- `business_phone`
- `business_address`
- `city`
- `state`
- `postal_code`
- `gst_number` nullable
- `verification_status`
- `verification_notes` nullable
- `approved_by` nullable foreign key to `users`
- `approved_at` nullable timestamp
- `created_at`
- `updated_at`

### Suggested Verification Status Values

- `pending`
- `approved`
- `rejected`
- `suspended`

## 3. Waste Category Pricing Table

### Table

`waste_category_pricing`

### Purpose

Store sell-side default pricing by category for fixed-price listing creation.

### Required Fields

- `id`
- `waste_category`
- `unit_price_per_kg`
- `is_active`
- `effective_from`
- `effective_to` nullable
- `created_by`
- `created_at`

## 4. Inventory Lots Table

### Table

`inventory_lots`

### Purpose

Represent collected material available for dealers to purchase.

### Required Fields

- `id`
- `pickup_request_id` unique foreign key to `pickup_requests`
- `citizen_id` foreign key to `users`
- `collector_id` foreign key to `users`
- `waste_category`
- `weight_kg`
- `unit_price_per_kg`
- `total_listed_amount`
- `source_address_snapshot`
- `source_city`
- `listing_status`
- `listed_at`
- `reserved_at` nullable
- `sold_at` nullable
- `expires_at` nullable
- `created_at`
- `updated_at`

### Suggested Listing Status Values

- `available`
- `reserved`
- `sold`
- `cancelled`
- `expired`

### Notes

- Address should be privacy-safe. Dealer should not see exact citizen details if not required.
- A snapshot is preferable so later edits to a pickup do not alter historical lot records.

## 5. Dealer Orders Table

### Table

`dealer_orders`

### Purpose

Track dealer reservations and purchases against inventory lots.

### Required Fields

- `id`
- `inventory_lot_id` foreign key to `inventory_lots`
- `dealer_user_id` foreign key to `users`
- `order_status`
- `quantity_kg`
- `unit_price_per_kg`
- `gross_amount`
- `commission_percent`
- `platform_revenue_amount`
- `payment_method`
- `payment_status`
- `admin_notes` nullable
- `reserved_at`
- `confirmed_at` nullable
- `fulfilled_at` nullable
- `cancelled_at` nullable
- `created_at`
- `updated_at`

### Suggested Order Status Values

- `reserved`
- `confirmed`
- `fulfilled`
- `cancelled`

### Suggested Payment Status Values

- `pending`
- `recorded_offline`
- `failed`

### Notes

- MVP can keep one order per lot for simplicity.
- Payment can remain manual while still recording commercial outcomes.

## 6. Optional Transaction Event Table

### Table

`dealer_order_events`

### Purpose

Track status changes and support auditability.

### Recommended for MVP

- yes, if engineering capacity allows
- otherwise rely on timestamps in `dealer_orders` and admin notes

## Data Integrity Rules

- A dealer cannot reserve a lot unless verification status is `approved`.
- A lot cannot be created unless the pickup is `completed` and has actual weight.
- A sold lot cannot return to `available` without admin action.
- Gross amount must equal `quantity_kg * unit_price_per_kg`.
- Platform revenue must equal `gross_amount * commission_percent`.

## API Endpoints Required

The current API contains `auth`, `pickup-requests`, `collector`, and `admin` routes. Dealer Marketplace MVP should add dealer-specific and marketplace-specific APIs.

## Authentication and Profile

### POST `/auth/register`

Extend registration flow to support `dealer` role, or allow admin-created dealer users.

### GET `/auth/me`

Return dealer role and verification state for authenticated dealer users.

## Dealer Profile APIs

### POST `/dealer/profile`

Create dealer business profile if not already present.

### GET `/dealer/profile`

Get dealer profile and verification status.

### PATCH `/dealer/profile`

Update editable business profile fields while pending or approved, subject to business rules.

## Dealer Marketplace APIs

### GET `/dealer/lots`

List available inventory lots for verified dealers.

### Query Parameters

- `status`
- `waste_category`
- `city`
- `min_weight_kg`
- `max_weight_kg`

### GET `/dealer/lots/{lot_id}`

Get detailed information for one inventory lot.

### POST `/dealer/lots/{lot_id}/reserve`

Reserve an available lot at the listed fixed price.

### GET `/dealer/orders`

List the dealer's reservations and purchases.

### GET `/dealer/orders/{order_id}`

Get dealer order details.

## Admin Dealer Management APIs

### GET `/admin/dealers`

List dealer accounts and verification states.

### GET `/admin/dealers/{dealer_id}`

Get dealer profile detail for review.

### POST `/admin/dealers/{dealer_id}/approve`

Approve dealer verification.

### POST `/admin/dealers/{dealer_id}/reject`

Reject dealer verification.

### POST `/admin/dealers/{dealer_id}/suspend`

Suspend dealer marketplace access.

## Admin Pricing APIs

### GET `/admin/pricing`

List waste category pricing.

### POST `/admin/pricing`

Create pricing row.

### PATCH `/admin/pricing/{pricing_id}`

Update active pricing row.

## Admin Inventory APIs

### GET `/admin/inventory-lots`

List lots across all statuses.

### GET `/admin/inventory-lots/{lot_id}`

Get lot detail and linked request context.

### POST `/admin/inventory-lots/{lot_id}/cancel`

Cancel invalid or unsellable lot.

## Admin Order APIs

### GET `/admin/dealer-orders`

List all dealer orders.

### GET `/admin/dealer-orders/{order_id}`

Get order detail.

### POST `/admin/dealer-orders/{order_id}/confirm`

Confirm the reserved order.

### POST `/admin/dealer-orders/{order_id}/fulfill`

Mark the order fulfilled and commercially completed.

### POST `/admin/dealer-orders/{order_id}/cancel`

Cancel the order.

## Admin Reporting APIs

### GET `/admin/revenue/summary`

Return dealer commerce metrics for selected date range.

### GET `/admin/revenue/transactions`

Return transaction ledger rows for reporting.

### GET `/admin/revenue/export`

Export completed dealer transactions.

## Frontend Pages Required

The frontend currently routes to citizen, collector, and admin dashboards only. Dealer Marketplace MVP requires a new dealer dashboard and supporting admin pages.

## Dealer Pages

### 1. Dealer Registration or Activation Flow

### Purpose

Allow dealer account creation or profile completion.

### Key Content

- business name
- contact person
- phone
- address
- city and state
- GST number optional
- verification status message

### 2. Dealer Dashboard Home

### Purpose

Landing page for verified and pending dealers.

### Key Content

- verification status
- available lots count
- reserved lots count
- completed purchases count
- quick links to browse marketplace and orders

### 3. Dealer Marketplace Listings Page

### Purpose

Browse available lots.

### Key Content

- filters for category, city, and weight
- cards or table for lots
- status badges
- price per kg
- total lot value

### 4. Dealer Lot Details Page

### Purpose

Show enough information to make a purchase decision.

### Key Content

- waste category
- weight
- city or service area
- listed price
- total value
- reserve action

### 5. Dealer Orders Page

### Purpose

Track reserved, confirmed, fulfilled, and cancelled orders.

### Key Content

- order timeline
- status
- amount
- lot references

## Admin Pages

### 6. Admin Dealer Verification Page

### Purpose

Review and approve dealer onboarding.

### Key Content

- pending dealer list
- business profile details
- approve, reject, suspend actions

### 7. Admin Pricing Management Page

### Purpose

Manage price per waste category.

### Key Content

- pricing table
- add or update price
- effective date visibility

### 8. Admin Inventory Lots Page

### Purpose

See available, reserved, sold, and cancelled lots.

### Key Content

- linked pickup request
- category
- weight
- price
- lot status

### 9. Admin Dealer Orders Page

### Purpose

Manage reservations through fulfillment.

### Key Content

- dealer name
- order status
- gross amount
- platform revenue
- confirm and fulfill actions

### 10. Admin Revenue Reporting Page

### Purpose

Track startup revenue readiness.

### Key Content

- gross marketplace value
- dealer transaction count
- platform revenue
- verified dealer count
- export option

## Recommended UX Constraints for MVP

- No map dependency
- No chat dependency
- No real-time status updates required
- No multi-step negotiation workflow
- No dealer-visible citizen PII beyond coarse source area

## Acceptance Criteria

## Commercial Outcome Criteria

- One dealer can be created, verified, and activated.
- One completed pickup can become one dealer-visible inventory lot.
- One verified dealer can reserve that lot.
- Admin can confirm and fulfill the order.
- System can report gross transaction value and platform revenue for that order.

## Functional Acceptance Criteria

### AC-1 Dealer Onboarding

- A dealer account can be created.
- Dealer cannot reserve lots until verification status is approved.
- Dealer sees a clear pending or approved state in the product.

### AC-2 Inventory Generation

- A completed pickup with actual weight creates a lot or can be converted into one by admin.
- Lot contains category, weight, price, and status.

### AC-3 Dealer Browse and Reserve

- Verified dealer can view available lots.
- Dealer can reserve exactly one available lot.
- Reserved lot is no longer available to other dealers.

### AC-4 Admin Control

- Admin can approve dealer access.
- Admin can view and manage lot and order states.
- Admin can cancel invalid lots or orders.

### AC-5 Revenue Recording

- Confirmed dealer order stores gross value and commission value.
- Revenue data appears in admin reporting.

### AC-6 Auditability

- Admin can trace a dealer order back to the original pickup and collector.
- Historical order amounts do not change if later pricing changes.

## Risks and Dependencies

## Key Risks

### Risk 1: Supply quality inconsistency

Completed pickups may not yet produce standardized or dealer-trustworthy inventory.

### Mitigation

Keep the MVP limited to clearly categorized recyclable waste and manual admin oversight.

### Risk 2: Dealer trust gap

First dealers may hesitate if supply quality, quantity, or consistency is unclear.

### Mitigation

Use verified pilot lots and fixed pricing for the first transactions.

### Risk 3: Overbuilding a marketplace

Auction, bidding, chat, logistics, and automated payments can delay launch.

### Mitigation

Restrict the MVP to fixed-price reservations and offline settlement recording.

### Risk 4: Data model expansion complexity

Adding dealer, lot, pricing, and order entities increases migration and analytics complexity.

### Mitigation

Keep one order per lot and one lot per completed pickup for the MVP.

### Risk 5: Privacy leakage

Dealer views could accidentally expose citizen details.

### Mitigation

Expose only city or coarse source area in lot views.

## Dependencies

- agreement on initial waste category taxonomy
- agreement on default category pricing
- agreement on platform commission percentage
- actual weight capture at pickup completion
- admin capacity to manually verify dealers and orders during MVP
- product decision on self-serve dealer registration versus admin-created dealer accounts

## Recommended Product Decisions

To optimize for speed and first revenue, make these decisions before build starts:

1. Start with only one new role: `dealer`
2. Use fixed-price lots, not dealer bidding
3. Use offline settlement recording, not online payments
4. Auto-create lots from completed pickups with weight
5. Require admin verification before dealer purchasing
6. Use one lot per pickup and one order per lot in MVP

## Definition of Done

Dealer Marketplace MVP is done when Waste-IQ can demonstrate this live:

1. admin verifies a dealer
2. collector completes a pickup with weight
3. system produces a sellable lot
4. dealer reserves the lot
5. admin fulfills the order
6. platform reports the revenue from that transaction
