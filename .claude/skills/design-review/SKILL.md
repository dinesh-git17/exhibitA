---
name: design-review
description: Review engineering design documents for architectural gaps, missing constraints, vague requirements, incomplete dependency analysis, unrealistic scalability claims, and undefined failure handling. Use when reviewing a design doc, RFC, ADR, or technical proposal. Triggers on design document review, architecture review, RFC review, design critique, or technical proposal evaluation.
---

# Design Review

Review any engineering design document against the canonical Design Document Architecture Standard defined in `references/design-doc-standard.md`. Produce a structured gap report with severity-graded findings and concrete remediation guidance.

## Activation

Execute this skill when:
- A user provides a design document, RFC, ADR, or technical proposal for review.
- A user asks to validate, critique, or check an engineering design.
- A user references `/design-review` or asks for architecture review.

Do NOT execute when the document is a product requirements document, marketing brief, or non-engineering artifact. State the refusal reason and stop.

## Review Workflow

### Phase 1: Structural Validation

Parse the document and map its content against the twelve mandatory sections (S1-S12) from `references/design-doc-standard.md`. For each section, assign one status:

1. **Complete** — Section exists and meets all validation rules.
2. **Incomplete** — Section exists but fails one or more validation rules.
3. **Missing** — Section absent entirely.

Produce a structural compliance matrix:

```
Section              | Status      | Validation Failures
---------------------|-------------|---------------------
S1. Metadata Header  | Complete    | —
S2. Context          | Incomplete  | No quantitative data point
S3. Goals            | Missing     | —
```

### Phase 2: Technical Depth Analysis

For each present section, evaluate against these checks:

**S2 Context:** Named components described. Quantitative system data referenced. Prior docs linked.

**S3 Goals:** Every goal measurable with specific threshold. Prioritized P0/P1/P2. No unquantified subjective language.

**S4 Non-Goals:** Concrete capabilities excluded. Rationale per entry. No contradictions with S3.

**S5 Overview:** Under 500 words. No implementation details. Core proposal statable in one sentence.

**S6 Detailed Design:**
- S6.1: Components diagrammed with data flows and trust boundaries.
- S6.2: API schemas, error codes, backward compatibility analysis.
- S6.3: Schema changes with migration strategy, storage estimates, rollback.
- S6.4: Algorithm descriptions, state machines, concurrency model.
- S6.5: Deployment topology, resource requirements, feature flags.

**S7 Cross-Cutting Concerns:**
- S7.1 Security: STRIDE analysis, trust boundaries, data classification.
- S7.2 Observability: SLIs (P50/P95/P99), SLOs with rationale, alerting strategy.
- S7.3 Reliability: Failure modes, degradation strategy, blast radius.
- S7.4 Privacy: Data subject rights if PII involved.

**S8 Capacity Planning:** Back-of-envelope calculations with units. Projections at 2x/5x/10x. Bottleneck identified. Scaling strategy with cost.

**S9 Alternatives:** Minimum two with trade-off analysis. Each has at least one advantage. "Do nothing" evaluated. Comparison matrix present.

**S10 Dependencies/Risks:** Dependencies have fallback behavior. Risks have likelihood/impact/mitigation.

**S11 Migration Plan:** Multi-phase rollout. Rollback procedure with time estimate. Monitoring gates referencing SLIs.

**S12 Open Questions:** Each question has owner and target date. No duplication of resolved content.

### Phase 3: Anti-Pattern Detection

Scan for these failure modes:

| Anti-Pattern | Detection Signal |
|---|---|
| The Novel | >8000 words without proportional structural depth |
| The Handwave | Detailed Design has only prose, no diagrams/schemas/calculations |
| Strawman Alternatives | Every alternative has zero stated advantages |
| Assumed Scalability | Claims horizontal scaling without capacity math |
| Security Afterthought | S7.1 says "follow best practices" with no threat identification |
| Observability Vacuum | S7.2 absent or contains no SLI definitions |
| Missing Migration | No rollout plan or single-phase deployment |
| Orphaned Dependencies | Dependencies listed without fallback behavior |
| Vague Non-Goals | Non-goals are not concrete capabilities |
| Goal Without Metric | Goals use subjective language without measurable criteria |

### Phase 4: Gap Report

Produce the report in this structure:

```
# Design Review Report

## Document: [Title from S1]
## Reviewer: Claude (automated)
## Date: [current date]
## Verdict: [APPROVED | APPROVED WITH CONDITIONS | REVISION REQUIRED | REJECTED]

---

## Structural Compliance
[Matrix from Phase 1]

## Critical Gaps (P0 — Blocks Approval)
### [GAP-001] [Title]
- **Section:** S[N]
- **Finding:** [Specific gap]
- **Impact:** [What breaks or is unverifiable]
- **Remediation:** [Concrete fix with specifics]

## Major Gaps (P1 — Must Fix Before Implementation)
[Same structure]

## Minor Gaps (P2 — Should Fix)
[Same structure]

## Observations (Informational)
[Non-blocking notes]

## Anti-Patterns Detected
[List with references]

## Validation Checklist
- [ ] All S1-S12 present or justified as N/A
- [ ] Every goal has measurable success criterion
- [ ] At least two alternatives with trade-offs
- [ ] Security includes STRIDE-based threat identification
- [ ] Observability defines SLIs with target percentiles
- [ ] Capacity includes back-of-envelope calculations
- [ ] Migration has multi-phase rollout with rollback
- [ ] Every dependency has fallback behavior
- [ ] Every risk has likelihood, impact, and mitigation
```

## Severity Definitions

| Level | Meaning | Verdict Impact |
|---|---|---|
| P0 Critical | Architectural flaw, missing security/capacity/failure analysis | REJECTED or REVISION REQUIRED |
| P1 Major | Incomplete section, weak alternatives, missing migration phases | APPROVED WITH CONDITIONS |
| P2 Minor | Style issues, missing examples, minor omissions | APPROVED with recommendations |
| Info | Non-blocking suggestions | No verdict impact |

## Verdict Rules

- **REJECTED:** S2, S3, S5, S6, S7, S9, or S11 missing with no justification.
- **REVISION REQUIRED:** One or more P0 gaps present.
- **APPROVED WITH CONDITIONS:** No P0 gaps, one or more P1 gaps.
- **APPROVED:** No P0 or P1 gaps.

## Intelligent Questioning Protocol

When review identifies gaps unresolvable from the document, use AskUserQuestion to gather missing information.

### Batching Rules
- Collect all questions before presenting. Never ask one at a time.
- Group by subsystem or dependency, not by section number.
- Maximum four question groups per interaction.
- If more gaps exist, prioritize by severity and defer lower-priority questions.

### Priority Order
1. **Architectural blockers** — Answers change the fundamental design.
2. **Constraint clarifications** — Unstated requirements (latency bounds, consistency guarantees).
3. **Dependency resolutions** — External system behavior assumptions.
4. **Scope clarifications** — Goal/non-goal boundaries.

### Question Quality
- Every question must yield a fact, number, or binary choice as its answer.
- Never ask "add more detail to section X" — ask the specific question whose answer constitutes that detail.
- Never ask questions answerable from the document.
- Frame with context: state what the document says or omits and why it matters.

## Refusal Conditions

Refuse to review and state the reason if:
- Input is not an engineering design document.
- Input is under 200 words.
- Input contains no identifiable technical proposal.
- Document metadata shows `Deprecated` or `Superseded` status.

State: `Review refused: [reason]. Provide an engineering design document for review.`

## Reference

Canonical section definitions and validation rules: `references/design-doc-standard.md`.
