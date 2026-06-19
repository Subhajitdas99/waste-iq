# Waste-IQ Dealer Marketplace MVP Delivery Plan

## Objective

Deliver Dealer Marketplace MVP in 2 weeks with the narrowest scope required to support:

- first paying dealer
- first completed waste transaction
- startup launch readiness

## GitHub Issues

These issues are sequenced for implementation and can be created as separate GitHub issues under a `Dealer Marketplace MVP` milestone.

### WIQ-DM-001 Add dealer role to auth and permissions model

**Purpose**
Support a dedicated buyer role without overloading admin or collector access.

**Scope**

- add `dealer` role definition
- update auth and access matrix
- define protected views for dealer users

**Acceptance Criteria**

- Dealer can authenticate successfully
- Dealer cannot access admin-only routes
- Existing citizen, collector, and admin access remains unchanged

### WIQ-DM-002 Create dealer profile and verification workflow

**Purpose**
Introduce trusted buyer onboarding.

**Scope**

- create dealer profile data model
- support pending, approved, rejected, and suspended states
- expose admin approval workflow

**Acceptance Criteria**

- Dealer profile can be created and reviewed
- Unapproved dealer cannot reserve lots
- Admin can approve and reject a dealer profile

### WIQ-DM-003 Add waste category pricing management

**Purpose**
Enable fixed-price marketplace listings.

**Scope**

- create category pricing model
- add admin create, edit, and view flows
- define pricing history behavior

**Acceptance Criteria**

- Admin can set active price per category
- Listing price uses the current active category price
- Historical sold orders preserve applied pricing

### WIQ-DM-004 Require reliable weight capture at pickup completion

**Purpose**
Ensure inventory can be generated from completed pickups.

**Scope**

- validate actual weight capture
- confirm completed pickup data quality
- prepare linkage to inventory lot creation

**Acceptance Criteria**

- Pickup cannot become sellable inventory without actual weight
- Weight is stored and traceable to pickup and collector

### WIQ-DM-005 Generate inventory lots from completed pickups

**Purpose**
Turn operational pickups into dealer-visible supply.

**Scope**

- create inventory lot entity
- map completed pickup to one lot
- define lot status lifecycle

**Acceptance Criteria**

- Completed pickup creates one inventory lot
- Available lot shows category, weight, price, and status
- Invalid or cancelled lots are not dealer-visible

### WIQ-DM-006 Build dealer marketplace listing and details views

**Purpose**
Enable verified dealers to discover available supply.

**Scope**

- marketplace list page
- filters for category, city, and weight
- lot details page

**Acceptance Criteria**

- Verified dealer can browse available lots
- Dealer can open lot details and see fixed price and total value
- Pending dealer cannot access purchase actions

### WIQ-DM-007 Add dealer reserve-lot order flow

**Purpose**
Create the first commercial transaction path.

**Scope**

- reserve order creation
- one order per lot logic
- dealer order history

**Acceptance Criteria**

- Dealer can reserve an available lot
- Reserved lot is blocked from other dealers
- Dealer can see order status in order history

### WIQ-DM-008 Build admin lot and dealer order management

**Purpose**
Give operators control during early launch.

**Scope**

- admin inventory page
- admin order list and detail view
- confirm, fulfill, and cancel actions

**Acceptance Criteria**

- Admin can view all lots and all dealer orders
- Admin can confirm and fulfill dealer reservations
- Admin can cancel invalid orders with status recorded

### WIQ-DM-009 Add dealer revenue reporting and export

**Purpose**
Measure commercial traction from the first transaction.

**Scope**

- gross marketplace value
- platform revenue
- dealer transaction count
- export ledger

**Acceptance Criteria**

- Admin can view dealer commerce KPIs
- Export includes lot, dealer, gross value, and commission data
- Metrics reconcile with dealer orders

### WIQ-DM-010 Run launch-readiness QA and pilot script

**Purpose**
Ensure the new workflow is demoable and operationally safe.

**Scope**

- end-to-end QA checklist
- first dealer transaction demo script
- launch blocker log

**Acceptance Criteria**

- Team can complete one end-to-end dealer transaction in staging
- Critical blockers are resolved or explicitly accepted

## Shared Acceptance Criteria

- Dealer Marketplace MVP can be demonstrated end-to-end in staging
- Exactly one dealer order can be traced from pickup completion to revenue reporting
- Admin can manage dealer verification, lot states, and order states without database intervention
- Dealer-facing pages do not expose citizen PII beyond permitted location summary

## 2-Week Sprint Plan

Assumption:

- one backend engineer
- one frontend engineer
- one shared QA and founder review loop

## Week 1

### Day 1

- Finalize scope lock
- Confirm product decisions on dealer onboarding, fixed pricing, and offline settlement
- Create GitHub milestone and issues

### Day 2

- Complete data model design review
- Finalize role and permissions matrix
- Finalize dealer profile and pricing requirements

### Day 3

- Implement or prepare backend work for dealer role, dealer profile, and pricing model
- Start admin approval workflow design

### Day 4

- Implement or prepare backend work for inventory lots and order entities
- Define state transitions for lots and dealer orders

### Day 5

- Backend API review for dealer browse, reserve, and admin order actions
- Frontend design review for dealer dashboard and admin pages
- Mid-sprint demo of non-UI workflow readiness

## Week 2

### Day 6

- Build dealer-facing pages for dashboard, listings, and lot details
- Build admin dealer verification page

### Day 7

- Build dealer orders page
- Build admin inventory and order management pages

### Day 8

- Build admin revenue reporting view
- Complete API integration and error-state handling

### Day 9

- Execute end-to-end QA
- Run founder walkthrough for first paying dealer scenario
- Fix critical defects

### Day 10

- Run launch-readiness checklist
- Freeze scope
- Prepare staging demo and production go-live decision

## Sprint Deliverables

- dealer role live in product
- dealer onboarding and verification
- inventory lots generated from completed pickups
- dealer reservation flow
- admin confirmation and fulfillment flow
- revenue reporting for dealer orders

## Sprint Exit Criteria

- A verified dealer can sign in and reserve a lot
- An admin can fulfill that lot and record the transaction
- Revenue appears in reporting
- The team can demo the workflow without manual database editing

## Out of Scope for This Sprint

- WhatsApp alerts
- GPS tracking
- AI classification
- live bidding
- payment gateway integration
- recycler workflows
- municipality feature expansion
