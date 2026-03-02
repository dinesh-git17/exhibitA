# Design Document Architecture Standard

Internal engineering standard defining the canonical structure, required content, and validation rules for all engineering design documents.

---

## S1. Metadata Header

**Purpose:** Establish document identity, ownership, lifecycle state, and review tracking.

**Required Content:**

| Field         | Format                                                                            | Example                                                   |
| ------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Title         | Imperative, under 80 characters                                                   | `Migrate payment processing to event-driven architecture` |
| Author(s)     | Name (team)                                                                       | `J. Chen (Payments)`                                      |
| Reviewers     | Name (role)                                                                       | `K. Patel (Security), M. Wu (SRE)`                        |
| Status        | Enum: `Draft`, `In Review`, `Accepted`, `Implemented`, `Superseded`, `Deprecated` | `In Review`                                               |
| Created       | ISO 8601 date                                                                     | `2026-02-20`                                              |
| Last Updated  | ISO 8601 date                                                                     | `2026-02-23`                                              |
| Supersedes    | Link to prior doc or `N/A`                                                        | `N/A`                                                     |
| Superseded By | Link to successor doc or `N/A`                                                    | `N/A`                                                     |

**Validation Rule:** All eight fields present. Status is a valid enum value. Dates are valid ISO 8601. Author and Reviewer lists are non-empty.

---

## S2. Context

**Purpose:** Establish objective facts about the current state of the system, business domain, and technical landscape. No opinions. No advocacy. The reader must understand the existing world before evaluating the proposed change.

**Required Content:**

- Current system architecture relevant to the proposal (component names, data flows, dependencies).
- Business context: why this area matters, what user-facing behavior exists today.
- Technical debt or constraints inherited from prior decisions.
- Recent incidents, performance data, or capacity trends motivating the change.
- Links to prior design docs, ADRs, or RFCs that inform this proposal.

**Validation Rule:** Contains at least three concrete, verifiable facts about the current system. No forward-looking statements. No solution language. References at least one quantitative data point (latency, error rate, cost, traffic volume).

---

## S3. Goals

**Purpose:** Define the measurable outcomes this design must achieve. Goals are the acceptance criteria for the design itself.

**Required Content:**

- Numbered list of specific, measurable objectives.
- Each goal includes a success metric or completion criterion.
- Goals are ordered by priority (P0, P1, P2).

**Validation Rule:** Minimum two goals. Each goal contains a quantitative or binary success criterion. No goal uses subjective language ("improve," "better," "faster") without a measurable threshold.

---

## S4. Non-Goals

**Purpose:** Explicitly exclude objectives that a reasonable reviewer might assume are in scope. Non-goals prevent scope creep and align reviewer expectations.

**Required Content:**

- Numbered list of things this design deliberately does not address.
- Each non-goal includes a one-sentence rationale for exclusion.
- Non-goals must be plausible goals — not strawmen.

**Validation Rule:** Minimum one non-goal. Each entry is a concrete capability or behavior, not a restatement of "we won't do X" without specifying X. No non-goal contradicts a stated goal.

---

## S5. Overview

**Purpose:** Provide a high-level summary of the proposed change in 2-4 paragraphs. A senior engineer unfamiliar with the project should understand the core idea after reading only this section.

**Required Content:**

- What changes at the system level (new components, modified interfaces, removed dependencies).
- The primary architectural pattern or approach chosen.
- Key trade-offs acknowledged at the summary level.

**Validation Rule:** Under 500 words. No implementation details (no class names, function signatures, or config snippets). A reader can state the core proposal in one sentence after reading this section.

---

## S6. Detailed Design

**Purpose:** Describe the proposed system changes with sufficient precision for implementation and review. This is the core of the document.

**Required Content:**

### S6.1 System Architecture

- Component diagram showing new and modified components.
- Data flow between components with protocol and format specified.
- System boundaries and trust boundaries marked.

### S6.2 API Design

- Interface contracts for all new or modified APIs (request/response schemas, error codes).
- Backward compatibility analysis: breaking changes identified, migration path defined.
- Versioning strategy if applicable.

### S6.3 Data Model

- Schema changes with field types, constraints, and indexes.
- Data migration strategy (expand-contract pattern preferred).
- Storage estimation: current volume, projected growth at 1-year and 3-year horizons.
- Data retention and deletion policies.

### S6.4 Core Logic

- Algorithm descriptions for non-trivial business logic.
- State machine diagrams for stateful workflows.
- Concurrency model: locking strategy, race condition mitigations.

### S6.5 Infrastructure

- Deployment topology changes.
- Resource requirements (compute, memory, storage, network).
- Configuration and feature flag strategy.

**Validation Rule:** Each subsection present if the design touches that domain. Every new component has a defined owner. Every API has at least one example request/response pair. Data model changes include rollback strategy. No subsection is empty or contains only prose with no specifics.

---

## S7. Cross-Cutting Concerns

**Purpose:** Address system-wide properties that span components. These are first-class design elements, not afterthoughts.

**Required Content:**

### S7.1 Security

- Authentication and authorization model for new surfaces.
- Data classification for all stored and transmitted data (PII, credentials, internal, public).
- Trust boundary analysis: where untrusted input enters the system.
- STRIDE threat assessment for modified attack surfaces.

### S7.2 Observability

- SLIs: specific metrics this system will emit (latency P50/P95/P99, error rate, throughput).
- SLOs: target values with rationale grounded in user impact.
- Alerting strategy: what triggers a page vs. a ticket vs. a dashboard annotation.
- Logging: structured log schema, sampling strategy, retention period.
- Tracing: span definitions, propagation across service boundaries.

### S7.3 Reliability

- Failure modes: enumerated list of what can go wrong.
- Degradation strategy: behavior under partial failure.
- Recovery procedures: manual and automated.
- Blast radius: what is affected if this system fails entirely.
- SLA impact on upstream and downstream dependencies.

### S7.4 Privacy and Compliance

- Data subject rights handling (access, deletion, portability).
- Regulatory requirements applicable to stored data.
- Audit trail requirements.

**Validation Rule:** Security section includes at least one threat identified via STRIDE. Observability section defines at least three SLIs. Reliability section enumerates at least two failure modes with mitigations. Privacy section present if any PII is stored or processed.

---

## S8. Capacity Planning

**Purpose:** Validate that the proposed design can handle projected load. Prevent designs that work at prototype scale but fail at production scale.

**Required Content:**

- Current baseline metrics: traffic (RPS), storage (GB), compute utilization.
- Projected metrics at 2x, 5x, and 10x current load.
- Back-of-envelope calculations showing the math behind resource estimates.
- Bottleneck identification: which component saturates first under load.
- Horizontal vs. vertical scaling strategy with cost implications.

**Validation Rule:** Contains at least one numeric calculation with units. Projections cover at least two growth scenarios. Bottleneck analysis identifies at least one limiting resource. No unsubstantiated claims ("this will scale" without math).

---

## S9. Alternatives Considered

**Purpose:** Document other viable approaches and the explicit reasoning for rejecting them. This is among the highest-value sections for future readers.

**Required Content:**

- Minimum two alternatives to the proposed design.
- Each alternative includes:
  - Brief description of the approach.
  - Advantages over the proposed design.
  - Disadvantages or risks.
  - Explicit reason for rejection.
- Comparison matrix covering: complexity, cost, timeline, risk, scalability, operational burden.

**Validation Rule:** At least two alternatives described with trade-off analysis. "Do nothing" counts as one alternative. Each alternative has at least one stated advantage (not strawmen). Rejection reasons are specific, not "too complex" without explaining what complexity means in context.

---

## S10. Dependencies and Risks

**Purpose:** Enumerate external dependencies and risks that could block, delay, or compromise the design.

**Required Content:**

### S10.1 Dependencies

- Upstream services: what this design consumes, SLA expectations, fallback behavior if unavailable.
- Downstream consumers: what depends on this system, backward compatibility commitments.
- Third-party dependencies: vendor services, libraries, external APIs with versioning constraints.
- Team dependencies: other teams whose work must land before or concurrently.

### S10.2 Risks

- Technical risks: unproven technology, complex migrations, performance unknowns.
- Organizational risks: team capacity, knowledge gaps, competing priorities.
- Timeline risks: hard deadlines, external commitments, regulatory dates.
- Each risk includes: likelihood (High/Medium/Low), impact (High/Medium/Low), mitigation strategy.

**Validation Rule:** At least one dependency and one risk documented. Every dependency specifies fallback behavior. Every risk has a mitigation strategy. No risk is listed without both likelihood and impact assessed.

---

## S11. Migration and Rollout Plan

**Purpose:** Define how the proposed change moves from accepted design to production deployment with controlled risk.

**Required Content:**

- Phased rollout plan with percentage-based traffic shifting or feature flag gates.
- Rollback procedure: specific steps, expected rollback time, data consistency guarantees.
- Backward compatibility window: how long old and new systems coexist.
- Monitoring gates: metrics that must remain healthy before advancing each phase.
- Data migration strategy if applicable (expand-contract, dual-write, backfill).

**Validation Rule:** Rollout has at least two phases (not big-bang). Rollback procedure exists and specifies maximum rollback time. Monitoring gates reference specific SLIs from S7.2.

---

## S12. Open Questions

**Purpose:** Transparently surface decisions not yet made. Prevents reviewers from assuming the author has answers they do not.

**Required Content:**

- Numbered list of unresolved decisions.
- Each question identifies who is responsible for resolving it and the target resolution date.
- Questions grouped by subsystem or dependency.

**Validation Rule:** If present, every question has an owner and a target date. Questions do not duplicate content already resolved in the Detailed Design. An empty Open Questions section is acceptable only if S6-S11 are fully resolved.

---

## Anti-Patterns and Failure Modes

| Anti-Pattern                  | Description                                               | Detection Signal                                          |
| ----------------------------- | --------------------------------------------------------- | --------------------------------------------------------- |
| **The Novel**                 | Document exceeds 20 pages without clear structure         | Word count > 8000; no headings map to standard sections   |
| **The Handwave**              | Critical sections contain only prose with no specifics    | Detailed Design lacks diagrams, schemas, or calculations  |
| **The Strawman Alternatives** | Alternatives section lists only obviously bad options     | Every alternative has zero stated advantages              |
| **Assumed Scalability**       | Claims system "scales horizontally" without capacity math | S8 missing or contains no numeric calculations            |
| **Security Afterthought**     | Security section says "will follow best practices"        | S7.1 contains no STRIDE analysis or threat identification |
| **Observability Vacuum**      | No SLIs, SLOs, or alerting strategy defined               | S7.2 missing or contains only "we will add monitoring"    |
| **Missing Migration**         | Design proposes changes with no rollout plan              | S11 absent or says "deploy to production"                 |
| **Orphaned Dependencies**     | External dependencies listed without fallback behavior    | S10.1 entries lack degradation strategy                   |
| **Vague Non-Goals**           | Non-goals are generic ("not building a perfect system")   | S4 entries are not concrete capabilities                  |
| **Goal Without Metric**       | Goals use subjective language without measurable criteria | S3 entries lack quantitative success criteria             |
