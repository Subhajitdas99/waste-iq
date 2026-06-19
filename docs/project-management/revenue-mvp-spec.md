# Waste-IQ Revenue MVP Specification

## Document Purpose

Define the minimum product changes required to turn Waste-IQ into a revenue-generating marketplace without expanding into AI or broad enterprise scope.

## Problem

Waste-IQ supports pickup operations but does not yet support monetization-ready transaction capture. Completed pickups do not appear to create a commercially meaningful record for:

- estimated material value
- actual collected weight by category
- buyer value realization
- platform commission
- payout and settlement tracking

## Product Goal

Enable Waste-IQ to record, measure, and report revenue for every completed pickup.

## Non-Goals

- AI waste classification
- automated price prediction
- full payment gateway integration
- dynamic route optimization
- municipality-specific custom workflows
- auction or live bidding engine

## Users

### Citizen

Creates pickup requests and expects pricing transparency.

### Collector

Completes pickups and records actual collected quantity.

### Admin

Defines pricing, reviews transactions, and tracks platform revenue.

## Scope

### In Scope

- Admin-managed pricing table by waste category
- Estimated value displayed at request creation or request detail stage
- Actual weight capture during completion
- Completed transaction record
- Platform commission calculation
- Revenue analytics and export

### Out of Scope

- automated payment disbursement
- buyer marketplace matching
- municipal dashboards beyond current admin analytics

## Core Workflow

1. Citizen creates a pickup request with waste type and address details.
2. Platform uses admin-configured pricing to estimate transaction value.
3. Collector accepts and completes the request with actual weight.
4. System calculates final transaction value using recorded weight and category price.
5. System calculates platform commission using admin-configured rules.
6. Admin can view transaction ledger and revenue analytics.

## Functional Requirements

### FR-1 Pricing Configuration

Admin can define a base rate per kilogram for each waste category supported in the marketplace.

### FR-2 Estimated Value Preview

Citizen sees an estimated material value before or after request submission when sufficient category and quantity information exists.

### FR-3 Completion Weight Capture

Collector must record actual collected weight before marking a pickup as completed.

### FR-4 Transaction Record

Every completed pickup generates a transaction record linked to the pickup request, citizen, collector, waste category, actual weight, unit rate, gross value, and commission value.

### FR-5 Commission Rules

Admin can configure a commission model for the MVP.

Recommended MVP rule:

- flat percentage take rate across all categories

### FR-6 Revenue Analytics

Admin dashboard shows:

- total gross marketplace value
- total platform revenue
- number of monetized pickups
- average value per completed pickup

### FR-7 Export

Admin can export completed transaction records as CSV for reconciliation and investor reporting.

## Data Requirements

### New Data Objects

- WasteCategoryPricing
- CompletedTransaction
- CommissionConfiguration

### Minimum Transaction Fields

- pickup_request_id
- citizen_id
- collector_id
- waste_category
- actual_weight_kg
- unit_price_per_kg
- gross_transaction_value
- commission_percent
- platform_revenue_value
- completed_at

## API and UI Implications

### Backend

- Pricing management endpoints for admin
- Completion flow updates to require weight and compute transaction values
- Revenue analytics endpoints
- Transaction export endpoint

### Frontend

- Admin pricing management UI
- Admin revenue dashboard cards and tables
- Collector completion form enhancements
- Citizen request value visibility

## Acceptance Criteria

### AC-1 Pricing Setup

- Admin can create and update a price per waste category.
- Invalid or incomplete pricing inputs are rejected with clear validation.

### AC-2 Completion Gating

- Collector cannot complete a pickup without entering actual weight.
- Weight input is stored with the completed transaction.

### AC-3 Revenue Calculation

- When a pickup is completed, the platform calculates gross value and commission automatically.
- Calculated values remain visible in admin reporting.

### AC-4 Reporting

- Admin dashboard displays gross marketplace value and total platform revenue for a chosen date range.
- Counts reconcile with completed transaction records.

### AC-5 Export

- Admin can download a CSV of monetized transactions.
- Export includes the minimum transaction fields listed in this spec.

## Dependencies

- Stable waste category taxonomy
- Clear ownership of pricing operations
- Admin dashboard extension capacity
- Agreement on initial commission percentage

## Risks

### Risk 1

If quantity is not captured early, estimated value may be misleading.

### Response

Allow estimate messaging to remain clearly approximate until collector completion.

### Risk 2

Collectors may enter inconsistent weights without verification.

### Response

Treat weight as operationally entered data in MVP and introduce verification later.

### Risk 3

Commission disputes may arise if price logic is unclear.

### Response

Keep the MVP commission rule simple, fixed, and visible to internal operators.

## Recommended Delivery Sequence

1. Pricing data model and admin configuration
2. Collector completion flow update
3. Transaction ledger generation
4. Revenue analytics
5. Export and reconciliation workflow

## Launch Decision

Revenue MVP is launch-ready when the team can answer these questions from product data alone:

1. How many pickups generated revenue this week?
2. What was gross marketplace value?
3. What was platform commission revenue?
4. Which waste categories contributed most value?
5. Which collectors completed the highest-value pickups?
