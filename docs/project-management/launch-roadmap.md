# Waste-IQ Launch Roadmap

## Objective

Turn Waste-IQ from a working waste pickup MVP into a revenue-generating startup optimized for:

1. Fast pilot launch with collectors and citizens
2. Early B2B revenue from scrap dealers and recyclers
3. Municipality pilot readiness with reporting and oversight
4. Delaying AI features until the commercial workflow is proven

## Current Product Status

### Implemented

- Authentication
- Citizen dashboard
- Collector dashboard
- Admin dashboard
- Pickup lifecycle management
- Basic analytics
- Production deployment

### Not Yet Implemented

- Scrap dealer role
- Recycler role
- Municipality role and pilot workflows
- Pricing and quote flow
- Payments and settlement records
- Buyer demand marketplace
- Commercial reporting
- SLA and operations tooling
- Automated test coverage

## Launch Strategy

Revenue should come from completed recyclable transactions before advanced AI is introduced.

### Revenue Sequence

1. Commission per completed transaction
2. Monthly subscription for verified buyers
3. Paid municipality dashboard pilot
4. AI-assisted pricing or classification as an upsell after workflow adoption

## Milestones

## Milestone 0: Launch Hardening

### Goal

Stabilize the existing citizen to collector workflow so pilots do not fail operationally.

### Why First

No monetization layer will matter if pickup operations are unreliable, untracked, or difficult to support.

### Deliverables

- Production readiness checklist
- Role and permission audit
- Error handling and support visibility
- Event and activity audit trail validation
- Basic QA regression checklist
- Pilot operations dashboard metrics

### Exit Criteria

- Core auth and pickup lifecycle works end-to-end in staging and production
- Admin can identify stuck requests and inactive collectors
- Team has a repeatable smoke test for every release
- Top production risks are documented with owners

## Milestone 1: Revenue MVP

### Goal

Monetize the existing workflow by introducing price capture, completed transaction value, and commission tracking.

### Why This Is the First Revenue Step

Waste-IQ already supports a pickup lifecycle. The shortest path to revenue is to convert completed pickups into measurable commercial transactions.

### Deliverables

- Waste category pricing model
- Pickup request estimated value
- Collector completion with actual weight and payout inputs
- Admin commission configuration
- Transaction ledger for completed pickups
- Revenue analytics for completed transactions and commissions

### Exit Criteria

- Every completed pickup stores transaction value and platform revenue
- Admin can export revenue data for billing and reporting
- Founders can compute take rate and gross marketplace value weekly
- Pilot partners can validate price transparency

## Milestone 2: Buyer Marketplace MVP

### Goal

Enable scrap dealers and recyclers to express demand and receive matched supply from completed collections.

### Why Second

This creates the two-sided marketplace necessary for recurring B2B revenue and stronger unit economics.

### Deliverables

- New buyer roles: scrap dealer and recycler
- Buyer onboarding and verification workflow
- Demand listings by material, location, and minimum quantity
- Matching view for available collected material
- Admin approval flow for verified buyers
- Buyer analytics and lead funnel tracking

### Exit Criteria

- At least one buyer can register, get verified, and create demand
- Admin can view supply and demand coverage by category
- Team can manually match collected waste to buyers during pilot

## Milestone 3: Municipality Pilot Package

### Goal

Package Waste-IQ as an operational intelligence layer for one municipality pilot.

### Why Third

Municipality sales cycles are longer. This should follow once transaction and buyer workflows are proven in a live operating environment.

### Deliverables

- Municipality dashboard role
- Ward or zone level metrics
- Request completion and diversion reports
- Collector performance reporting
- CSV export for pilot review
- Pilot SLA tracking

### Exit Criteria

- Municipality user can access a read-only operational dashboard
- Team can produce weekly pilot reports without manual spreadsheet reconstruction
- Founders can demonstrate diversion and service performance metrics in sales meetings

## Milestone 4: Workflow Automation and AI Readiness

### Goal

Add AI only after the core transaction engine and buyer network are functioning.

### Deliverables

- Waste image classification backlog
- Price recommendation experiments
- Collector recommendation engine
- Demand forecasting research

### Exit Criteria

- AI roadmap is tied to measurable operational pain points
- Training data sources and labeling workflow are defined
- No AI work blocks core marketplace revenue

## Recommended Implementation Order

1. Launch hardening
2. Revenue MVP
3. Buyer marketplace MVP
4. Municipality pilot package
5. AI readiness

## Team Operating Cadence

### Weekly Rhythm

- Monday: backlog review and milestone status
- Wednesday: blocker review and pilot metrics check
- Friday: demo, production risk review, and next sprint lock

### Suggested Sprint Length

- 1 week until launch hardening is complete
- 2 week sprints after monetization work begins

## Progress Tracker

| Area | Status | Notes |
| --- | --- | --- |
| Citizen workflow | Green | Implemented and deployed |
| Collector workflow | Green | Implemented and deployed |
| Admin analytics | Green | Implemented, likely needs expansion |
| Revenue model in product | Red | Not implemented |
| Buyer marketplace | Red | Not implemented |
| Municipality reporting | Red | Not implemented |
| Automated testing | Red | No visible test suite |
| Pilot operations tooling | Yellow | Partial via admin and request lifecycle |

## Success Metrics

### Launch Metrics

- Pickup request completion rate
- Average time from request creation to collector acceptance
- Average time from acceptance to completion
- Active collectors per week
- Repeat citizen usage rate

### Revenue Metrics

- Gross marketplace value
- Completed pickups with recorded transaction value
- Platform commission revenue
- Revenue per collector per month
- Verified buyers onboarded

### Municipality Metrics

- Pickup completion by zone
- Material volume by category
- Collector SLA compliance
- Diversion volume reported

## Top Risks

### Risk 1: No monetization in current workflow

The product currently enables pickups but does not clearly capture transaction value or platform revenue.

### Mitigation

Prioritize Milestone 1 before any net-new AI or advanced dashboards.

### Risk 2: Missing B2B buyer side

Without scrap dealer and recycler workflows, Waste-IQ behaves more like an operations app than a true marketplace.

### Mitigation

Build buyer onboarding and demand posting immediately after revenue capture.

### Risk 3: Municipality scope creep

Municipality features can expand into a separate enterprise product and delay launch.

### Mitigation

Keep municipality scope limited to reporting, oversight, and exports for the first pilot.

### Risk 4: Weak QA and release confidence

No visible automated tests increase launch risk as role complexity grows.

### Mitigation

Require smoke test coverage and critical path regression checklists in Milestone 0.

### Risk 5: Collector supply reliability

A marketplace fails if citizen demand is created before dependable collector response exists.

### Mitigation

Track collector acceptance and completion metrics before scaling acquisition.
