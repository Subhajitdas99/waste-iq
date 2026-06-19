# Waste-IQ GitHub Issue Backlog

This backlog is ordered by recommended implementation sequence.

## Epic 1: Launch Hardening

### WIQ-001 Audit role permissions across citizen, collector, and admin flows

**Why**
Reduce launch risk from unauthorized access or role confusion.

**Tasks**

- Review route and UI access for every current role
- Document expected permissions matrix
- Identify gaps between backend enforcement and frontend visibility

**Acceptance Criteria**

- Every existing route is mapped to an intended role
- Any mismatch between UI and backend access is documented
- Permission matrix is approved for launch

### WIQ-002 Create release smoke test checklist for critical user journeys

**Why**
Provide a repeatable launch safety net before each production release.

**Tasks**

- Define smoke tests for register, login, create request, accept request, complete request, and admin analytics
- Assign owner and execution cadence
- Store checklist in repo docs

**Acceptance Criteria**

- Team can execute critical-path validation in under 30 minutes
- Checklist covers all implemented dashboards and lifecycle transitions

### WIQ-003 Add operations metrics for stuck and aging pickup requests

**Why**
Founders need visibility into operational failures during pilot.

**Tasks**

- Define stuck request states
- Add aging thresholds for pending and accepted jobs
- Surface counts in admin reporting

**Acceptance Criteria**

- Admin can identify pending requests older than target SLA
- Admin can identify accepted jobs not progressing to completion

## Epic 2: Revenue MVP

### WIQ-004 Create pricing model for waste categories

**Why**
Pricing is required to convert pickups into monetizable transactions.

**Tasks**

- Define supported waste categories for pricing
- Add admin-managed price per kilogram
- Document default pricing assumptions

**Acceptance Criteria**

- Admin can create and update category pricing
- Unsupported categories are blocked or flagged

### WIQ-005 Add estimated transaction value to pickup workflow

**Why**
Citizens and operators need pricing transparency before completion.

**Tasks**

- Decide whether quantity estimate is required or optional
- Show estimated value messaging in request flow
- Store estimate inputs for later comparison

**Acceptance Criteria**

- Citizen sees an estimated value when sufficient data is available
- Estimate is clearly marked as provisional

### WIQ-006 Require actual weight capture at collector completion

**Why**
Final transaction value depends on actual collected material quantity.

**Tasks**

- Update collector completion workflow
- Validate weight input
- Prevent completion when weight is missing

**Acceptance Criteria**

- Completed pickups always include actual weight
- Invalid weights are rejected with clear validation

### WIQ-007 Generate completed transaction ledger records

**Why**
Revenue cannot be tracked without durable transaction records.

**Tasks**

- Create transaction object and linkage rules
- Store unit rate, gross value, and commission value
- Define immutable completion-time pricing behavior

**Acceptance Criteria**

- Every completed monetized pickup creates one transaction record
- Historical records preserve the applied price and commission

### WIQ-008 Add admin commission configuration

**Why**
Platform take rate must be measurable and configurable.

**Tasks**

- Define simple MVP commission rule
- Add admin controls and validation
- Document versioning behavior for changed commission settings

**Acceptance Criteria**

- Admin can set a valid commission percentage
- New completed transactions use the active commission rule

### WIQ-009 Expand admin analytics with GMV and revenue metrics

**Why**
Leadership needs commercial visibility, not just operations counts.

**Tasks**

- Add gross marketplace value metrics
- Add platform revenue metrics
- Add monetized pickup count and average value

**Acceptance Criteria**

- Admin dashboard displays commercial KPIs
- Metrics reconcile with transaction ledger data

### WIQ-010 Export monetized transaction data as CSV

**Why**
Founders need reconciliation, investor reporting, and pilot reporting support.

**Tasks**

- Define CSV schema
- Add export action in admin workflow
- Validate date range handling

**Acceptance Criteria**

- Admin can export monetized transactions for a selected period
- Export includes weight, price, gross value, and commission fields

## Epic 3: Buyer Marketplace MVP

### WIQ-011 Add scrap dealer and recycler account roles

**Why**
Waste-IQ needs buyer-side participants to become a true marketplace.

**Tasks**

- Define buyer role taxonomy
- Decide self-serve versus admin-created onboarding
- Specify verification requirements

**Acceptance Criteria**

- System supports buyer role creation and access control
- Admin can distinguish verified and unverified buyers

### WIQ-012 Build buyer onboarding and verification workflow

**Why**
Commercial counterparties must be screened before participating.

**Tasks**

- Collect business profile details
- Define document requirements
- Add admin review status flow

**Acceptance Criteria**

- Buyer cannot access marketplace actions until approved
- Admin can approve or reject verification

### WIQ-013 Create buyer demand listing workflow

**Why**
Buyers need a structured way to express what material they want.

**Tasks**

- Define listing fields for category, quantity, location, and price preference
- Create lifecycle states for active and inactive demand
- Add admin visibility

**Acceptance Criteria**

- Verified buyer can create a demand listing
- Admin can view active demand across categories

### WIQ-014 Build supply-demand matching view for operators

**Why**
Manual matching is acceptable for MVP, but it must be visible in product.

**Tasks**

- Define matching rules
- Surface completed or available material against demand
- Allow internal operators to track match status

**Acceptance Criteria**

- Admin can see candidate buyers for collected material
- Team can manage pilot matches without external spreadsheets

## Epic 4: Municipality Pilot Package

### WIQ-015 Add municipality dashboard role

**Why**
Pilot stakeholders need controlled access without giving them admin privileges.

**Tasks**

- Define municipality role permissions
- Decide read-only access scope
- Add access management rules

**Acceptance Criteria**

- Municipality users can sign in and view only approved reporting pages
- Municipality users cannot alter marketplace operations

### WIQ-016 Build zone-level pilot reporting

**Why**
Municipality buyers care about operational insight by geography, not just platform totals.

**Tasks**

- Define zone or ward grouping model
- Add key pilot metrics by geography
- Create weekly reporting view

**Acceptance Criteria**

- Municipality dashboard shows pickup and completion metrics by zone
- Pilot stakeholders can review material movement trends

### WIQ-017 Add municipality export and reporting pack

**Why**
Pilots often require offline review and procurement documentation.

**Tasks**

- Define export formats
- Align with municipality meeting cadence
- Add summary-ready fields

**Acceptance Criteria**

- Team can export municipality-ready operational data without manual reformatting

## Epic 5: AI Readiness

### WIQ-018 Define AI feature gating policy after revenue MVP

**Why**
AI work should follow business proof, not replace it.

**Tasks**

- Document launch prerequisites for AI work
- Define measurable triggers for starting AI scope
- Rank AI ideas by commercial leverage

**Acceptance Criteria**

- Team has a clear rule for when AI work begins
- AI backlog is ordered by revenue and pilot value

## Suggested Sprint Order

### Sprint 1

- WIQ-001
- WIQ-002
- WIQ-003
- WIQ-004

### Sprint 2

- WIQ-005
- WIQ-006
- WIQ-007

### Sprint 3

- WIQ-008
- WIQ-009
- WIQ-010

### Sprint 4

- WIQ-011
- WIQ-012

### Sprint 5

- WIQ-013
- WIQ-014

### Sprint 6

- WIQ-015
- WIQ-016
- WIQ-017
