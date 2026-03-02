# Exhibit A - Custom Application Proposal

**Prepared for:** Client  
**Prepared by:** Freelance Software Consultant  
**Date:** March 2, 2026  
**Project:** Exhibit A (iOS app + backend + admin panel)

## 1. Executive Summary

This proposal covers design-aligned implementation of Exhibit A as a private, high-quality custom application spanning:

- Native iOS app experience
- FastAPI backend and data layer
- Admin web panel for content operations
- Push notifications, offline behavior, and signature workflows

The delivery approach is phased, production-minded, and focused on reliability, maintainability, and user-facing polish.

## 2. Project Scope

The implementation includes the following in-scope workstreams.

### A. Backend Platform

- FastAPI service and SQLite schema implementation
- App-facing authenticated APIs for content, signatures, sync, and device registration
- Signature upload handling and conflict behavior
- Authentication and signer identity controls
- Deployment templates for Caddy, systemd, and Litestream backup replication

### B. Admin Panel

- Session-based admin authentication
- Dashboard and content management surfaces
- Create, edit, reorder, and delete workflows for contracts, letters, and thoughts
- APNS trigger on new content publication

### C. iOS Application

- SwiftUI app foundation, navigation shell, and state model
- Theme and design token implementation
- Home, Letters, and Thoughts experiences
- Contract Book with page-curl container, dynamic pagination, and final-page sequencing
- PencilKit signature capture and signed-state rendering

### D. Sync, Offline, and Integration

- Launch and background sync flows
- Push registration and route-driven deep link handling
- Offline signature upload queue with retry and reconciliation logic

### E. Polish and Release Readiness

- Sound settings and cue service
- Haptics and animation wiring
- QA hardening across core feature flows

## 3. Deliverables

1. Production-ready source code for iOS, backend, and admin panel aligned to the project design and phase documents.
2. Configured project structure and deployment artifacts for backend hosting workflow.
3. Implemented signature, sync, push, and offline flows as specified in scope.
4. Validation artifacts: lint/test compliance and smoke-test coverage for core paths.
5. Handover documentation for setup, environment, and operational continuity.

## 4. Commercials

**Total Project Fee (Fixed): $100,000 USD**

Suggested milestone billing:

1. Milestone 1 (Foundation and Backend): $25,000
2. Milestone 2 (Admin + iOS Core Features): $30,000
3. Milestone 3 (Contract Book + Signatures + Sync): $30,000
4. Milestone 4 (Polish, QA, Release Handover): $15,000

## 5. Timeline Framing

Estimated delivery window: **16 to 20 weeks**, executed in phased milestones corresponding to the defined roadmap.

Timeline assumes:

- Timely client feedback and acceptance at milestone checkpoints
- Stable scope with controlled change requests
- Required credentials and access provided without delay

## 6. Assumptions

1. Scope is based on the current design and phase documentation and remains materially stable.
2. Third-party accounts and credentials (Apple Developer, APNS key materials, infrastructure access) are
   client-provided.
3. Content strategy and legal text are client-provided; implementation covers rendering, storage, and management
   workflows.
4. Final release operations follow agreed deployment workflow and environment constraints.

## 7. Exclusions

The following are out of scope unless added through formal change order:

1. Android application development
2. Public App Store launch and marketing assets
3. Multi-tenant user system beyond intended two-signer model
4. New major feature areas not defined in current scope documents
5. Ongoing post-launch retainer support beyond agreed stabilization window

## 8. Change Control

Any request that expands scope, alters architecture, or adds net-new feature surfaces will be handled via written change
order including:

1. Impact on timeline
2. Impact on budget
3. Revised acceptance criteria

No expanded work is executed without written approval.

## 9. Acceptance and Warranty

1. Each milestone is reviewed against explicit acceptance criteria from agreed scope artifacts.
2. A 30-day post-delivery stabilization window is included for defect remediation tied to in-scope functionality.
3. Enhancements or new features requested after acceptance are treated as new scope.

## 10. Terms

1. Pricing is in USD.
2. Invoices are due within 7 calendar days.
3. Work may pause on overdue invoices until account status is current.
4. Proposal validity: 14 days from issue date.

## 11. Evaluation Sources

Pricing and proposal framing were informed by the following market and estimation references (accessed March 2, 2026):

1. Clutch software development pricing guide: <https://clutch.co/developers/pricing>
2. Clutch mobile app development pricing guide: <https://clutch.co/directory/mobile-application-developers/pricing>
3. Upwork hourly rate guidance: <https://www.upwork.com/resources/upwork-hourly-rates>
4. Arc freelance software developer rate benchmarks: <https://arc.dev/freelance-developer-rates/software-development>
5. U.S. Bureau of Labor Statistics software developer outlook:
   <https://www.bls.gov/ooh/Computer-and-Information-Technology/Software-developers.htm>
6. GAO Cost Estimating and Assessment Guide: <https://www.gao.gov/products/gao-20-195g>
7. PandaDoc software proposal template guidance: <https://www.pandadoc.com/software-development-proposal-template/>
8. Proposify proposal template guidance: <https://www.proposify.com/proposal-templates>
9. Bonsai statement of work template guidance:
   <https://www.hellobonsai.com/scope-of-work-template/freelance-statement-of-work>
10. Jotform software SOW template guidance:
    <https://www.jotform.com/form-templates/software-development-statement-of-work-sow>

## 12. Next Step

Upon approval, execution begins with kickoff, access handoff, and Milestone 1 initiation.
