# ADR-017 — Agent Result Reconciliation and Controlled Integration

**Status:** Accepted  
**Document version:** 0.1.2  
**Architecture baseline:** AEW v0.1 with accepted orchestration extension  
**Accepted on:** 2026-11-26  
**Decision scope:** Agent Result Packages, combined candidates, verification and review binding, repository integration, and knowledge reconciliation

## 1. Context

Specialists can produce individually valid results that conflict when combined. Findings may disagree, patches may overlap, and changes to different files may alter shared behavior.

AEW needs a controlled path from specialist output to a verified Work Unit, with evidence linking each integration decision to its inputs and baseline. This decision builds on [ADR-003](ADR-003-revision-scoped-snapshots.md), [ADR-004](ADR-004-workspace-consistency.md), [ADR-009](ADR-009-context-packages.md), [ADR-010](ADR-010-controlled-execution.md), [ADR-011](ADR-011-work-units-and-delivery.md), [ADR-013](ADR-013-adaptive-multi-agent-orchestration.md), [ADR-014](ADR-014-composable-agent-profiles.md), [ADR-015](ADR-015-sandbox-isolation.md), and [ADR-016](ADR-016-coordination-and-delegated-authority.md).

## 2. Decision

Specialists submit immutable Agent Result Packages. An engine-controlled integration controller validates those packages and prepares a combined candidate in an isolated environment. Required verification and review bind to that exact immutable combined candidate. Candidate changes trigger evidence reassessment before repository application or delivery readiness.

### 2.1 Result packages

A versioned manifest identifies the assignment, parent execution, Work Unit, plan revision, repository baseline, Context Package, child authority record, and execution outcome. It references integrity-verifiable artifacts containing applicable changes, findings, evidence, verification results, and limitations.

Read-only assignments may submit findings without patches. Failed or cancelled assignments may submit partial evidence with their outcome recorded.

Corrections produce new package revisions with explicit lineage. The engine retains the original submission and its disposition.

### 2.2 Intake and reconciliation

The integration controller must:

- Validate package structure, artifact integrity, assignment identity, and provenance against engine records.
- Check actual changes against authorized scope and protected paths.
- Validate artifact paths and process submitted content within the isolation boundary.
- Establish baseline compatibility and identify textual and semantic conflicts.
- Record which contributions were accepted, rejected, deferred, or superseded, with reasons.

Artifact integrity establishes that content matches its recorded identity. Trusted engine records establish provenance and authority.

Conflicting findings remain visible until reconciled. Code changes require a recorded resolution before entering a verified candidate. Material changes to scope return to planning and authorization reassessment.

### 2.3 Combined candidate and verification

The controller constructs a candidate from explicitly selected package revisions and recorded integration changes. It records the resulting content identity, baseline, contributing artifacts, and resolution decisions.

Before verification or review, the engine validates the complete candidate diff against the baseline and the current task, plan, Work Unit, authorization, and protected-path rules. This check includes all conflict-resolution edits and other integration-generated changes. An unauthorized change blocks further progression until it is removed or the applicable authorization and plan are revised through their trusted mechanisms.

The validated candidate is frozen with an integrity-verifiable identity and workspace fingerprint. Any content change creates a new candidate identity and repeats the final-diff validation. Verification uses isolated materializations of the frozen candidate. Changes produced by tests or tools can enter a candidate only through a new candidate identity and revalidation.

Verification runs against the combined candidate. Specialist test results remain supporting evidence. Required checks must establish the behavior of the combined result.

Independent review follows the Work Unit's risk and verification requirements. Missing or failed required checks remain explicit and prevent a fully verified status.

Any candidate change requires reassessment of affected verification and review evidence. Evidence must identify the exact candidate it verifies or reviews. Required checks must pass against the new candidate, and required review acceptances must identify that new candidate before it can satisfy the application gate. Historical evidence retains its original candidate identity and cannot be relabeled as an observation of the new candidate.

Verification and review assignments receive an immutable Context Package identifying the baseline commit, coherent source Brain snapshot, candidate identity, and candidate workspace fingerprint. Baseline assertions retain their source provenance, with applicability to the candidate recorded or uncertainty made explicit. Only assertions established as applicable may be presented as current candidate facts. Candidate-derived findings are labeled with their candidate observation. Where the assignment's current package represents a different observation, the engine creates a successor package and explicitly validates execution rebinding under ADR-009 against the task, plan, authority, and workspace. A candidate change repeats that applicability assessment and context transition before verification or review continues.

### 2.4 Repository integration and recovery

Applying the candidate to the engineer's checkout requires authorization for that operation and current preflight evidence. The engine also requires every check mandated by the active plan and policy to have passed and every required review to have an accepted outcome, including human acceptance where required. It validates the integrity, provenance, and applicability of those records against the exact immutable candidate and current requirements. A missing, failed, incomplete, rejected, or stale required outcome blocks application and delivery readiness.

Immediately before application, the controller revalidates the complete candidate diff against current authority and protected paths, checks that its identity matches the verified and reviewed candidate, and validates the target baseline, workspace observations, and concurrency protections required by ADR-004. Drift or changed requirements require reassessment before application can proceed.

Application must preserve unrelated changes. If interrupted or partially completed, the controller records the observed state and reconciles it before retrying. Recovery must preserve modifications made by other actors.

After application, the controller confirms the applied change boundary and resulting scoped content against the approved candidate before recording application success. A mismatch is an unresolved application outcome requiring reconciliation.

The default remains one proposed commit per meaningful implementation Work Unit. Staging, committing, pushing, PR creation, and merging each require their applicable authorization.

### 2.5 Knowledge reconciliation

Candidate findings pass through Project Brain validation before publication. Accepted assertions retain provenance and explicit membership in a coherent revision-scoped snapshot. Snapshot publication follows ADR-003's atomicity requirements.

Findings derived from a candidate retain its identity and workspace fingerprint and cannot be presented as facts observed solely at the baseline commit. They remain candidate-scoped until their applicability to a target repository observation is established. Before inclusion in a committed-revision snapshot, the engine records the actual target commit and an applicability decision supported by relevant content and dependency comparisons or targeted verification. A different target commit or candidate requires reassessment. Unknown applicability remains explicit and prevents publication as current committed-revision knowledge. Published assertions and snapshots remain immutable, with corrections represented through new assertions or snapshot membership decisions.

## 3. Consequences

Combined candidates and their evidence remain traceable to specific specialist contributions and integration decisions. Reconciliation, verification, and review require resources within the authorized task budget. Changes to the candidate require evidence reassessment before delivery can proceed.

## 4. Verification criteria

- The engine rejects tampered artifacts, mismatched assignments, unauthorized paths, and incompatible baselines.
- The full candidate diff, including integration-generated changes, is checked against current authority and protected paths before verification or review and again immediately before application. An unauthorized resolution edit blocks progression.
- Conflicting findings and integration resolutions remain traceable.
- Required verification and review identify the exact immutable combined candidate. Candidate changes trigger evidence reassessment.
- A changed candidate receives a new identity, repeats final-diff validation, and cannot inherit required verification or review outcomes recorded only for the previous candidate. Test-generated edits cannot silently alter the candidate.
- Required combined-result checks are executed, and unavailable checks remain explicit.
- Missing, failed, incomplete, rejected, or stale required verification or review outcomes block application and delivery readiness, even when application is otherwise authorized.
- Candidate verification and review use candidate-specific immutable context. A changed observation requires applicability assessment and explicit context rebinding under ADR-009.
- Concurrent target changes are detected before application.
- Successful application requires a confirmed change boundary and scoped content matching the approved candidate.
- Interrupted application can recover without duplicate application or loss of unrelated work.
- Project Brain publication preserves assertion provenance and coherent snapshot membership.
- Candidate-derived findings retain their observation identity. They cannot enter a committed-revision snapshot as current knowledge until applicability to that actual commit is established and recorded.

## 5. Follow-on decisions

Agent Result Package schemas and their relationship to the Delivery Contract require review during a later implementation assignment. That review must also cover candidate-specific context bindings and the application gate across the Context, Approval, Execution, and Delivery contracts. Candidate identity representation, evidence retention, artifact storage, and guarded application mechanisms remain implementation decisions subject to these invariants.
