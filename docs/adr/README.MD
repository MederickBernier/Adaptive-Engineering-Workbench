# AEW — Architecture Decision Records

**Document:** `docs/adr/README.md`  
**Version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Last updated:** 2026-11-22  
**Status:** Decision registry

---

## 1. Purpose

This directory contains the Architecture Decision Records (ADRs) governing the Adaptive Engineering Workbench (AEW).

An ADR records a significant architectural decision, its context, rationale, consequences, and implementation invariants.

ADRs exist to preserve engineering intent across development sessions, contributors, and AI coding agents.

They answer four questions:

1. What problem required an architectural decision?
2. What decision was made?
3. Why was this approach selected?
4. What properties must implementation preserve?

The ADR registry is not an implementation backlog.

Implementation sequencing belongs in `docs/implementation-roadmap.md`.

The consolidated system design belongs in `docs/architecture.md`.

ADRs establish the decisions that constrain both.

---

## 2. Architectural Authority

Accepted ADRs are normative for the architecture they govern.

Implementation code, tests, and examples must conform to accepted decisions unless a subsequent accepted ADR explicitly supersedes them.

A working implementation does not automatically justify violating an ADR.

When implementation reveals a problem with an accepted decision, the appropriate response is to document the conflict and propose a revision.

### 2.1 Authority boundaries

ADRs establish architectural intent and invariants.

Versioned contracts establish machine-readable interfaces.

Repository security policy and explicit authorization govern restricted operations.

Implementation documents establish sequencing and operational guidance.

No ADR grants permission to perform repository modifications, execute commits, push branches, or publish pull requests.

### 2.2 Resolving conflicts

When an apparent conflict exists:

1. Identify the affected ADRs and contracts.
2. Determine whether the conflict is architectural, structural, or implementation-specific.
3. Preserve existing invariants while investigating.
4. Propose the smallest viable resolution.
5. Request review for material architectural changes.
6. Record an accepted superseding decision when necessary.

Do not silently change an accepted ADR to match an implementation shortcut.

---

## 3. Decision Registry

The following decisions form the current AEW v0.1 architectural baseline.

| ID | Decision | Status | Document |
|---|---|---|---|
| ADR-001 | Project Brain storage | Accepted | [ADR-001](ADR-001-project-brain-storage.md) |
| ADR-002 | Shared knowledge vault | Accepted | [ADR-002](ADR-002-knowledge-vault.md) |
| ADR-003 | Revision-scoped graph snapshots | Accepted | [ADR-003](ADR-003-revision-scoped-snapshots.md) |
| ADR-004 | Workspace consistency and concurrent modification protection | Accepted | [ADR-004](ADR-004-workspace-consistency.md) |
| ADR-005 | Git preflight and task branch strategy | Accepted | [ADR-005](ADR-005-git-preflight.md) |
| ADR-006 | Per-project intelligence profiles | Accepted | [ADR-006](ADR-006-project-intelligence-profile.md) |
| ADR-007 | Staged discovery and targeted invalidation | Accepted | [ADR-007](ADR-007-staged-discovery.md) |
| ADR-008 | Progressive knowledge depth | Accepted | [ADR-008](ADR-008-progressive-knowledge-depth.md) |
| ADR-009 | Immutable Context Packages | Accepted | [ADR-009](ADR-009-context-packages.md) |
| ADR-010 | Controlled execution and checkpoints | Accepted | [ADR-010](ADR-010-controlled-execution.md) |
| ADR-011 | Adaptive Work Units and delivery | Accepted | [ADR-011](ADR-011-work-units-and-delivery.md) |
| ADR-012 | Adaptive planning and event-driven approval | Accepted | [ADR-012](ADR-012-adaptive-planning.md) |

**Registry convention:** An accepted decision and a completed ADR document are different things.

All twelve records are present. ADR-001 and ADR-002 carry Accepted headers, while their approval sections still call for engineer confirmation. The registry status remains Unconfirmed pending that review.

---

## 4. Decision Summaries

### ADR-003 — Revision-Scoped Graph Snapshots

The Project Brain must maintain coherent, revision-scoped graph snapshots.

Knowledge assertions are immutable, and snapshot membership is explicit.

Historical snapshots must remain reproducible.

**Primary invariant:** A snapshot cannot silently combine incompatible repository revisions.

### ADR-004 — Workspace Consistency

AEW must preserve unrelated workspace modifications and detect concurrent changes before writing files.

Dirty worktrees require scope-aware assessment.

**Primary invariant:** AEW must not overwrite unrelated or unexpectedly modified files.

### ADR-005 — Git Preflight

Implementation requires read-only Git preflight.

Task branches are proposed from the latest verified integration baseline, using configurable naming conventions.

**Primary invariant:** Missing remote freshness or coordination evidence must not be interpreted as successful preflight.

### ADR-006 — Project Intelligence Profile

AEW must discover project-specific languages, frameworks, tooling, conventions, and architecture.

**Primary invariant:** Project characteristics must be derived from evidence rather than assumed from a universal template.

### ADR-007 — Staged Discovery

Project knowledge is acquired incrementally and invalidated selectively.

**Primary invariant:** Changes to one knowledge region must not automatically invalidate unrelated verified knowledge.

### ADR-008 — Progressive Knowledge Depth

Knowledge is investigated at levels D0 through D3 according to task requirements.

Freshness and depth are separate dimensions.

**Primary invariant:** Deep knowledge is not necessarily current, and current knowledge is not necessarily deep.

### ADR-009 — Immutable Context Packages

Task-relevant knowledge is delivered through immutable, revision-bound Context Packages containing provenance, evidence, coverage, and uncertainty.

**Primary invariant:** Context expansion must not mutate an existing package or silently mix revisions.

### ADR-010 — Controlled Execution

Execution is constrained by validated envelopes, trusted authorization, guarded operations, budgets, checkpoints, and evidence-backed verification.

**Primary invariant:** AI reasoning cannot override deterministic execution boundaries.

### ADR-011 — Adaptive Work Units and Delivery

Implementation is divided into meaningful Work Units.

Each Work Unit normally produces one proposed commit with title, body, and verification evidence.

Git publication is disabled by default.

**Primary invariant:** Preparing a delivery artifact does not authorize executing or publishing it.

### ADR-012 — Adaptive Planning

Planning uses Quick, Standard, Deep, and Explore profiles.

Approvals are scoped to relevant actions and plan revisions.

**Primary invariant:** Planning depth must reflect actual risk and uncertainty, while material changes trigger appropriate authorization reassessment.

---

## 5. Decision Relationships

ADRs are related, but they do not form a simple linear dependency chain.

The following relationships identify important implementation dependencies.

### 5.1 Project Brain

```text
ADR-003  Revision-scoped snapshots
    |
    +-- ADR-006  Project intelligence profiles
    |
    +-- ADR-007  Staged discovery
    |
    +-- ADR-008  Progressive knowledge depth
                  |
                  v
             ADR-009
          Context Packages
```

ADR-003 establishes the consistency foundation.

ADR-006, ADR-007, and ADR-008 define how knowledge is discovered, classified, and maintained.

ADR-009 packages relevant knowledge for engineering tasks.

### 5.2 Repository and execution safety

```text
ADR-004  Workspace consistency
    |
    +-- ADR-005  Git preflight
    |
    +-- ADR-010  Controlled execution
                  |
                  v
             ADR-011
          Work Unit delivery
```

ADR-004 establishes workspace protection requirements.

ADR-005 provides repository preflight evidence.

ADR-010 enforces execution boundaries.

ADR-011 governs delivery preparation and publication separation.

### 5.3 Planning and authorization

```text
ADR-009  Context Packages
    |
    v
ADR-012  Adaptive planning
    |
    +-- ADR-010  Execution authorization
    |
    +-- ADR-011  Work Units and delivery
```

Context informs planning.

Planning determines Work Units and authorization requirements.

Execution and delivery must remain bound to the approved plan.

These diagrams describe conceptual dependencies, not mandatory module imports or runtime call graphs.

---

## 6. ADR Lifecycle

Each ADR has one lifecycle status.

| Status | Meaning |
|---|---|
| Proposed | Decision is documented but not approved |
| Accepted | Decision is approved and normative |
| Superseded | Replaced by a later accepted decision |
| Deprecated | No longer recommended, but may remain relevant to existing implementations |
| Rejected | Proposal was considered but not adopted |
| Unconfirmed | Historical decision requires reconstruction or confirmation |

A document may additionally carry a documentation-completeness note such as `Draft`, `Under review`, or `Complete`.

Documentation completeness is not the same as decision status.

### 6.1 Acceptance

An ADR becomes accepted only after an explicit architectural decision.

Creating a Markdown file does not constitute acceptance.

### 6.2 Supersession

Accepted ADRs should not be silently rewritten to reverse their decisions.

A replacement ADR must:

- Reference the original.
- Explain why the previous decision is no longer appropriate.
- Define the new decision.
- Identify migration or compatibility consequences.
- Specify affected contracts and implementations.

The original record remains available for historical context.

### 6.3 Minor corrections

Editorial changes, broken-link corrections, and clarifications that preserve the decision may be applied without supersession.

Material semantic changes require architectural review.

---

## 7. Standard ADR Format

Individual ADRs should follow this structure:

```markdown
# ADR-XXX — Decision Title

**Status:** Accepted
**Date:** YYYY-MM-DD
**Architecture baseline:** AEW v0.1
**Decision scope:** Relevant subsystems

## 1. Context

Describe the engineering problem and constraints.

## 2. Decision

State the selected architecture precisely.

## 3. Rationale

Explain why the decision was selected.

## 4. Alternatives Considered

Document meaningful alternatives and tradeoffs.

## 5. Architectural Invariants

State properties implementations must preserve.

## 6. Consequences

Describe benefits, costs, and limitations.

## 7. Implementation Guidance

Identify component boundaries and expected behavior.

## 8. Verification

Define how compliance can be demonstrated.

## 9. Related Decisions and Contracts

Link applicable ADRs and contracts.

## 10. Open Questions

Record unresolved implementation details without
silently expanding the accepted decision.
```

### 7.1 Writing guidelines

ADRs should be precise enough to guide implementation but avoid prescribing unnecessary internal details.

Prefer behavioral requirements and invariants over speculative class hierarchies.

An ADR should explain architectural boundaries, not duplicate the entire implementation roadmap.

### 7.2 Alternatives and rationale

Only document alternatives that were actually discussed or can be clearly identified as reconstructed analysis.

Do not fabricate historical deliberations.

If the original rationale is incomplete, state that explicitly.

### 7.3 Verification requirements

Each ADR should include concrete tests or observable conditions.

For example:

- Can a historical snapshot be reconstructed?
- Can a revoked grant authorize execution?
- Can a task modify an unrelated dirty file?
- Can a Context Package change without changing identity?
- Can an incomplete preflight be reported as passed?

Verification criteria should be testable wherever practical.

---

## 8. ADR-to-Contract Mapping

The following table identifies the principal contract relationships.

| ADR | Relevant contracts |
|---|---|
| ADR-003 | Context |
| ADR-004 | Approval, Execution |
| ADR-005 | Task, Context |
| ADR-006 | Context |
| ADR-007 | Context |
| ADR-008 | Context |
| ADR-009 | Context |
| ADR-010 | Approval, Execution |
| ADR-011 | Task, Execution, Delivery |
| ADR-012 | Task, Approval, Execution |

These relationships are not exhaustive.

A contract may be affected by several architectural decisions.

When changing a contract, review all applicable ADRs rather than only the most obvious one.

---

## 9. ADR-to-Milestone Mapping

| ADR | Initial implementation milestone |
|---|---|
| ADR-003 | M2 — Project Brain |
| ADR-004 | M1 — Preflight; M5 — Controlled execution |
| ADR-005 | M1 — Repository preflight |
| ADR-006 | M2 — Project intelligence |
| ADR-007 | M2 — Discovery and invalidation |
| ADR-008 | M2 — Progressive knowledge depth |
| ADR-009 | M3 — Context Packages |
| ADR-010 | M5 — Controlled execution |
| ADR-011 | M4 — Work Units; M6 — Delivery |
| ADR-012 | M4 — Adaptive planning |

See `docs/implementation-roadmap.md` for complete milestones, dependencies, and acceptance criteria.

The milestone mapping does not authorize implementation.

---

## 10. Instructions for Codex

Codex should use this registry as an architectural navigation index.

### 10.1 Before implementation

1. Identify the current task and milestone.
2. Read `AGENTS.md`.
3. Read the relevant architecture sections.
4. Identify applicable ADRs using this index.
5. Read the individual ADR documents that exist.
6. Inspect the relevant contracts.
7. Inspect actual repository state.
8. Identify unresolved architectural ambiguities.

Do not assume pending ADR files exist.

### 10.2 During implementation

- Preserve accepted invariants.
- Keep changes scoped.
- Avoid unnecessary abstraction.
- Distinguish architectural requirements from implementation suggestions.
- Validate contract compatibility.
- Maintain traceability between decisions, implementation, and tests.

### 10.3 When encountering an architectural conflict

Codex must not silently replace an accepted decision.

Instead:

1. Identify the affected ADR.
2. Explain the conflicting requirement.
3. Provide evidence from implementation or testing.
4. Propose alternatives.
5. Recommend the smallest coherent correction.
6. Request review before material changes.

### 10.4 After implementation

Update relevant documentation when implementation changes behavior.

If an architectural decision is superseded, preserve the original ADR and link the replacement.

Do not mark an ADR verified merely because code was written.

---

## 11. Outstanding Decision Status Review

Confirm the acceptance history of ADR-001 and ADR-002 with the engineer and reconcile the record headers, approval sections, and registry after review.

---

## 12. Registry Maintenance

Update this index whenever:

- A new ADR is proposed.
- An ADR is accepted.
- A decision is superseded or deprecated.
- An ADR document is completed.
- A significant decision dependency changes.
- A contract relationship changes.
- An implementation milestone changes materially.

Keep decision status and document completion status accurate.

The registry should remain concise enough to serve as a navigation aid.

Detailed reasoning belongs in the individual ADRs.

---

## 13. Governing Principle

Architecture Decision Records preserve the engineering intent behind AEW.

Their purpose is not to prevent implementation changes or create unnecessary bureaucracy.

Their purpose is to ensure that changes are deliberate, traceable, and consistent with the system's fundamental guarantees.

**Architectural decisions should constrain unsafe shortcuts without constraining legitimate engineering improvement.**
