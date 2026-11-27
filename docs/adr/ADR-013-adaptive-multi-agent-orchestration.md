# ADR-013 — Adaptive Multi-Agent Orchestration

**Status:** Accepted  
**Document version:** 0.1.2  
**Architecture baseline:** AEW v0.1 with accepted orchestration extension  
**Accepted on:** 2026-11-26  
**Decision scope:** On-demand delegation, launch authority, and coordination

## 1. Context

AEW scales planning through Quick, Standard, Deep, and Explore profiles. A single agent can complete many Work Units. Independent investigations, specialized expertise, and independent verification can justify delegation. Each additional agent consumes shared resources and creates an execution boundary the engine must enforce.

The original v0.1 architecture deferred multi-agent orchestration. This accepted extension builds on [adaptive planning](ADR-012-adaptive-planning.md), [controlled execution](ADR-010-controlled-execution.md), [immutable Context Packages](ADR-009-context-packages.md), and [Work Units and delivery](ADR-011-work-units-and-delivery.md).

## 2. Decision

AEW may provision short-lived specialists on demand within an existing task and Work Unit. The orchestrator proposes assignments. The local engine validates and provisions each assignment, tracks its lifecycle, and enforces its authority and resource limits.

Every specialist launch must go through the AEW engine, including provider-native subagents. A provider adapter may execute a launch authorized by the engine only when it can enforce the assignment's restrictions. The engine must decline delegation when the provider permits specialist launches outside that path and those launches cannot be disabled. Specialists may request help through the orchestrator. Recursive spawning is disabled by default.

| Planning profile | Delegation default |
|---|---|
| Quick | Start with one agent. Delegate when a specific gap justifies the overhead. |
| Standard | Assign a specialist when the objective and expected result can be bounded. |
| Deep | Parallelize independent assignments. Assign verification independently of implementation when risk warrants it. |
| Explore | Allow parallel read-only investigations within approved scope. |

Before launch, the engine must:

1. Bind the assignment to its task, Work Unit, immutable Context Package, and repository baseline.
2. Validate the assignment against active authorization and policy. Return material scope changes to planning for approval reassessment.
3. Verify that the selected runtime can enforce the assignment's restrictions.
4. Reserve capacity against the parent task's remaining budget before provisioning, including when launch requests arrive concurrently.
5. Enforce finite task-wide limits on concurrent agents and total admitted launch attempts, with the accounting rules in [ADR-016](ADR-016-coordination-and-delegated-authority.md). Both limits must be established within trusted authority and policy before delegation begins.

If a prerequisite is unmet, the engine declines launch and records the reason.

Each specialist operates in an isolated environment and submits candidate findings, changes, or verification evidence. The engine records outcomes for reconciliation and preserves recorded evidence when an assignment is cancelled. Project Brain publication and repository integration remain controlled operations.

## 3. Verification criteria

- A Quick task can complete with one agent. An Explore assignment cannot write to source.
- Native and other specialist launches pass through engine validation. A provider that cannot prevent bypass launches is rejected for delegated execution.
- Concurrent launches cannot oversubscribe the parent task budget or agent-count limits. Missing count limits prevent delegation. Failed provisioning and replacement launches consume the total launch allowance, while duplicate requests count once under ADR-016.
- The engine declines an assignment if the runtime cannot enforce its restrictions.
- Cancellation preserves recorded evidence. Results and unresolved disagreements remain traceable to their assignments and baselines.

## 4. Follow-on decisions

Agent profile composition, sandbox isolation, delegated authority, and result reconciliation are governed by ADR-014 through ADR-017. Runtime and provider selection remain open. Implementation follows the future milestones in the roadmap and requires a separate assignment.
