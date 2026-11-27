# ADR-016 — Agent Coordination and Delegated Authority

**Status:** Accepted  
**Document version:** 0.1.2  
**Architecture baseline:** AEW v0.1 with accepted orchestration extension  
**Accepted on:** 2026-11-26  
**Decision scope:** Delegation permission, child authority records, coordination, budgets, revocation, and recovery

## 1. Context

Delegation creates concurrent participants working within a task's existing authority and resource limits. AEW needs enforceable rules for permission inheritance, assignment coordination, cancellation, and recovery.

[ADR-010](ADR-010-controlled-execution.md) establishes trusted authorization and guarded execution. [ADR-013](ADR-013-adaptive-multi-agent-orchestration.md), [ADR-014](ADR-014-composable-agent-profiles.md), and [ADR-015](ADR-015-sandbox-isolation.md) add engine-mediated launches, versioned profiles, and verified isolation boundaries.

## 2. Decision

The AEW engine owns authoritative assignment state, delegated permissions, budget accounting, and lifecycle transitions. The orchestrator proposes assignments and coordination actions through the engine.

Each assignment binds its identity to its parent execution, task, plan revision, Work Unit, Context Package, repository baseline, profile revision, sandbox configuration, and runtime capability evidence.

### 2.1 Delegated authority

Effective specialist permissions are the intersection of:

- The parent execution's currently valid authority.
- The selected role and profile's capability limits.
- The assignment's requested scope.
- The runtime's demonstrated enforcement capabilities.
- Applicable repository and engine policy.

Protected paths and explicit denials take precedence. Specialization labels cannot increase authority.

Delegation requires explicit permission in trusted authorization. The engine must establish trusted parent authority and validate that permission before launch. It records each child's authority in a traceable record identifying the parent authority, assignment, effective restrictions, and validity constraints. The engine validates the record and its delegation chain against current authority before allowing guarded operations. Structural schema validity alone is insufficient.

A child's validity cannot exceed its parent's validity. Specialists may submit requests for help, scope changes, or additional resources. The engine evaluates those requests against active authority. Recursive spawning remains disabled by default.

### 2.2 Coordination

Assignments exchange requests, progress, findings, and evidence through engine-mediated channels. The engine records sender identity, assignment identity, relevant baseline, and operation identity. Recipients treat message contents as task evidence. Messages that request actions pass through authorization checks.

Dependencies between assignments are explicit. Before dependent execution begins, the engine validates that required results are available and applicable to its baseline and context. Conflicts remain visible for reconciliation.

Verification and review handoffs identify the exact combined candidate and its workspace fingerprint. The engine validates the candidate-specific Context Package and any context transition under ADR-009 and ADR-017 before dependent execution begins.

Each specialist writes within its own isolated workspace. Repository integration follows ADR-017, including checks for semantic conflicts between changes to different paths.

### 2.3 Budgets and concurrency

The engine reserves resources before launch and enforces aggregate task limits alongside per-agent limits. Reservations and accounting must remain consistent under concurrent requests, retries, crashes, and recovery.

Provisioning failures release only capacity known to be unused. Restarts and checkpoint resumption retain recorded consumption. Budget redistribution operates within existing authority and the parent's remaining resources. Extensions require trusted authorization.

Every delegated task must have finite limits for concurrent agents and total admitted launch attempts, enforced across all its specialist assignments. Missing limits prevent delegation. Limits may be tightened by policy, and increases require a trusted authorization or policy decision within the parent authority.

The engine atomically reserves a concurrent slot and durably consumes one total launch allowance when admitting a new provisioning attempt. Failed provisioning and fresh provisioning for retries, replacements, or restarts each consume the total allowance. Completing or cancelling an assignment never refunds that cumulative count. Repeated delivery of the same request uses an engine-enforced idempotent identity and counts once. An intentionally new provisioning attempt receives a new identity and consumes another allowance.

Provisioning and live runtimes occupy concurrent slots. A suspended assignment retains its slot while its runtime remains live. A slot can be released only after the engine establishes that provisioning left no live runtime or that the runtime and its descendants have stopped. Uncertain outcomes retain their reservation until reconciled. Recovery preserves both counts. Resuming an existing runtime consumes no additional launch allowance, while reprovisioning consumes another allowance.

### 2.4 Revocation, cancellation, and recovery

The engine revalidates authority before guarded operations and checkpoint resumption. Parent revocation, expiration, or suspension prevents further child operations. Affected running operations are stopped through the runtime's cancellation mechanism, with outcomes recorded.

Adapters must demonstrate their cancellation behavior and limits. Uncertain operation outcomes require reconciliation before retries or resource reuse.

Withdrawal or loss of an applicable runtime evidence approval under ADR-015 blocks further guarded operations and triggers the same suspension and cancellation handling for affected assignments. Recorded review or verification cannot substitute for current execution authority or runtime eligibility.

Cancellation preserves collected evidence. Recovery restores authoritative assignment state and budget accounting before execution resumes.

## 3. Consequences

Delegation decisions and child operations remain traceable to trusted authority. Engine state, delegation records, runtime cancellation, and resource accounting require coordinated persistence and validation.

## 4. Verification criteria

- The engine rejects authority escalation, forged delegation records, expired parents, protected-path access, and unauthorized spawning.
- Missing explicit delegation permission prevents specialist launch.
- Child authority records identify their parent authority and assignment, and the engine validates the current delegation chain before guarded operations.
- Concurrent launches and duplicate requests cannot exceed resource limits or duplicate assignments and operations.
- Missing agent-count limits prevent delegation. Concurrent admissions enforce both count limits atomically. Failed provisioning, replacements, and fresh provisioning retries consume the total allowance, while duplicate requests count once.
- Suspended live runtimes retain concurrent slots. Failed or uncertain termination prevents slot release until reconciliation, including after recovery.
- Revocation during execution prevents further child operations and triggers runtime cancellation with recorded outcomes.
- Recovery preserves consumed budgets and reconciles uncertain outcomes before retrying operations.
- Candidate-specific handoffs require explicit context validation. Withdrawn runtime evidence approval blocks guarded operations and triggers lifecycle handling.

## 5. Follow-on decisions

Introducing delegation permission and child authority records requires reviewed contract changes during a later implementation assignment. Result reconciliation and controlled integration are governed by ADR-017. Authority record representation, trusted issuance mechanisms, and revocation propagation details remain implementation decisions subject to these invariants.
