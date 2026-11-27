# ADR-015 — Sandbox Isolation and Execution Environments

**Status:** Accepted  
**Document version:** 0.1.2  
**Architecture baseline:** AEW v0.1 with accepted orchestration extension  
**Accepted on:** 2026-11-26  
**Decision scope:** Specialist execution environments, runtime eligibility, isolation evidence, and lifecycle controls

## 1. Context

Specialists may execute repository code, build scripts, tests, and tools whose behavior is untrusted. Each assignment needs an enforceable boundary protecting the engineer's workspace, other assignments, credentials, and engine state.

The [implementation roadmap](../implementation-roadmap.md) records disposable container execution. This decision extends that foundation to specialist environments while retaining [ADR-010](ADR-010-controlled-execution.md)'s requirement that isolation claims match demonstrated enforcement. It complements [engine-mediated specialist launches](ADR-013-adaptive-multi-agent-orchestration.md) and [composable Agent Profiles](ADR-014-composable-agent-profiles.md).

## 2. Decision

The AEW engine provisions an isolated environment for every specialist assignment. Each environment has an identity, an immutable configuration, a repository baseline, an execution grant reference, resource limits, and a lifecycle controlled by the engine.

### 2.1 Isolation boundaries

| Area | Required boundary |
|---|---|
| Repository | A dedicated workspace derived from the recorded baseline. Writes stay within assignment scope. The primary checkout and other assignments' workspaces remain inaccessible for modification. |
| Process | The runtime enforces filesystem access, subprocess privileges, resource limits, and network policy. Repository code executes inside this boundary. |
| Authority | The specialist receives only the tool capabilities and credentials required by its assignment. Engine signing keys, authorization stores, runtime administration, and publication credentials remain under trusted host control. |
| Knowledge | The specialist receives its immutable Context Package and explicitly permitted evidence. It submits candidate findings through the engine for validation and reconciliation. |

A Git worktree may provide workspace separation when shared Git metadata is protected by the process boundary. Containers may provide process isolation when their configuration satisfies the declared threat model. Runtime eligibility depends on demonstrated enforcement.

### 2.2 Versioned runtime capabilities and evidence

Every runtime adapter must publish a versioned isolation capability description and verification evidence. The description identifies the adapter and runtime versions, supported operating environment, configuration, threat model, enforced boundaries, and known limitations. Evidence must identify the tested versions and configuration, the checks executed, and their observed outcomes.

The engine admits an assignment only when its isolation requirements fit the demonstrated boundary. It records the applicable capability description revision and evidence references with the assignment. A runtime or configuration change requires reassessment of evidence applicability before execution or resumption.

Runtime evidence requires an approval record issued through a trusted engineer interface or trusted policy mechanism outside specialist control. The record identifies its issuer, the integrity-verifiable capability description and evidence, the approved adapter and runtime versions, operating environment, configuration, and validity constraints. The engine validates issuer authenticity, integrity, applicability, and current approval status. Adapter-supplied evidence alone cannot establish eligibility. Evidence approval establishes runtime eligibility within its declared boundary and remains subject to the assignment's separate authorization.

The engine checks the approval before provisioning, guarded operations, and resumption. Changes to the approved versions, environment, or configuration require reassessment and an applicable trusted approval record. Approval can be withdrawn when an isolation claim becomes invalid. Withdrawal, expiration where specified, or inability to establish current approval blocks launches and further guarded operations using the affected boundary. Running assignments follow ADR-016's suspension, cancellation, and uncertain-outcome handling, with evidence retained. Withdrawal also triggers reassessment of verification and review evidence that relied on the affected isolation claim before that evidence can satisfy ADR-017's application gate.

### 2.3 Execution policy

- Network access is denied by default. Approved access uses bounded destinations and capabilities. Provider inference traffic goes through the trusted provider adapter, with the supplied context and external services recorded.
- Writable storage is limited to assignment workspace, scratch space, and result storage. Host mounts and credentials require explicit scope. Runtime administration sockets are inaccessible.
- The engine enforces limits on time, memory, CPU, subprocesses, and output storage, alongside task and agent budgets.
- Missing isolation capabilities cause provisioning to fail. Resumption requires authorization, baseline, and environment revalidation.

## 3. Lifecycle and evidence

The engine records provisioning, execution, termination, and cleanup outcomes. Cancellation, timeout, or budget exhaustion stops the assignment's processes and descendant processes. The engine preserves collected evidence before cleanup and reports cleanup failures.

Changes leave the environment as result artifacts tied to the assignment and baseline. Integration follows the controlled reconciliation process in ADR-017.

## 4. Consequences

Assignments can run only on adapters with applicable verification evidence. Runtime selection must account for the actual isolation needs of the assignment and the declared threat model. Verification and capability descriptions require maintenance as adapters and operating environments evolve.

## 5. Verification criteria

- An assignment cannot modify the primary checkout or another assignment's workspace, access host credentials or runtime administration, escape write scope through filesystem links, or reach unauthorized network destinations.
- Resource limits are enforced and descendant processes stop on cancellation, timeout, or budget exhaustion.
- Collected evidence survives cleanup. Cleanup failures are recorded and reported.
- The engine refuses launch when required controls or applicable verification evidence are unavailable.
- The assignment records the capability description revision and evidence references. Runtime or configuration changes trigger reassessment of their applicability.
- Forged, altered, withdrawn, expired, or inapplicable runtime evidence approvals are rejected. Adapter-supplied evidence without a trusted approval cannot admit an assignment.
- Withdrawal of runtime evidence approval blocks launches and guarded operations, triggers lifecycle handling for affected running assignments, and requires reassessment of affected verification and review evidence before application.

## 6. Follow-on decisions

Runtime and operating-system selection remain open. Delegated authority and result reconciliation are governed by ADR-016 and ADR-017. Runtime capability, evidence approval record, and sandbox schemas require a later implementation assignment and contract review.
