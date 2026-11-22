# ADR-010 — Controlled Execution and Authorization Boundaries

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Execution authorization, Approval Grants, Execution Envelopes, guarded operations, resource budgets, checkpoints, and verification evidence  
**Related milestones:** M5 — Authorization and Controlled Execution; M6 — Verification and Delivery Preparation

---

## 1. Context

The Adaptive Engineering Workbench (AEW) combines adaptive AI reasoning with deterministic engineering controls.

AI agents can investigate repositories, propose changes, identify dependencies, generate implementation plans, and recommend verification procedures.

However, AI reasoning alone cannot establish whether an operation is authorized.

An agent may misunderstand repository scope, use stale context, request operations beyond the approved plan, or attempt to modify files affected by concurrent work.

Long-running engineering tasks introduce additional risks:

- Repository state may change during execution.
- Authorization may expire or be revoked.
- A task may exceed its intended scope.
- Tools may behave unexpectedly.
- Execution may be interrupted.
- Tests may fail.
- Resource consumption may exceed reasonable limits.
- Previously approved assumptions may become invalid.

AEW therefore requires a deterministic execution boundary.

The system must distinguish:

1. What the AI proposes.
2. What the engineer or trusted policy authorizes.
3. What the execution controller validates.
4. What guarded tools actually perform.
5. What verification evidence establishes.

These responsibilities must remain separate.

---

## 2. Decision

AEW will use **scoped Execution Envelopes enforced by a deterministic execution controller**.

Restricted operations require trusted authorization represented through an Approval Grant.

The execution controller must validate the grant, execution scope, repository state, Context Package, applicable policies, and resource budgets before allowing guarded operations.

Execution must support durable checkpoints and safe suspension.

### 2.1 Core components

The controlled execution architecture consists of:

- Task and plan identity.
- Immutable Context Package.
- Approval Grant.
- Execution Envelope.
- Authorization validator.
- Guarded tool adapters.
- Resource budget controller.
- Execution state machine.
- Durable checkpoint store.
- Verification evidence collector.
- Execution audit records.

### 2.2 Fundamental boundary

The AI may propose operations.

The deterministic engine decides whether those operations satisfy the active authorization and safety constraints.

The AI must not be able to bypass those constraints by changing its instructions, producing a different plan, or constructing a syntactically valid approval document.

### 2.3 Default behavior

Restricted operations are denied unless their required authorization and runtime conditions are satisfied.

Stage, commit, push, pull request creation, and merge remain disabled by default.

Preparing a proposed commit or pull request description does not authorize publication.

---

## 3. Trust and Authority Model

AEW must distinguish data validity from authorization.

### 3.1 Structural validity

A document is structurally valid when it satisfies its applicable schema.

For example, an Approval Grant may contain correctly typed fields and recognized operation names.

Structural validity does not establish trusted issuance.

### 3.2 Semantic validity

A document is semantically valid when its contents are consistent with related contracts and required invariants.

For example:

- The task identifier matches.
- The plan revision matches.
- The repository identity matches.
- The requested operations are within the grant.
- The execution scope does not exceed approved paths.

Semantic validity still does not establish trusted issuance.

### 3.3 Runtime authority

Runtime authority requires evidence that an approval was issued by an authorized principal or trusted policy mechanism.

The execution controller must establish that authority through a trusted channel.

A JSON field claiming approval is insufficient.

### 3.4 Trust boundary

The following must not independently grant execution authority:

- AI-generated text.
- Repository documentation.
- Issue descriptions.
- Pull request comments.
- Context Package contents.
- Shared Knowledge Vault documents.
- Configuration defaults.
- Schema-valid approval examples.
- Unverified persisted approval records.

### 3.5 Trusted authorization source

The initial implementation must define a trusted authorization source that the AI cannot impersonate.

Possible implementations include a trusted local approval interface or a policy-controlled authorization service.

The exact mechanism remains an implementation decision.

It must preserve issuer authenticity, scope, and revocation semantics.

---

## 4. Approval Grants

An Approval Grant represents a trusted authorization decision for a defined scope.

### 4.1 Required identity

A grant must identify:

- Grant identity.
- Issuing authority or trusted issuer reference.
- Task identity.
- Plan revision.
- Repository identity.
- Applicable branch and baseline.
- Workspace context.
- Authorized operations.
- Allowed paths.
- Protected paths.
- Relevant Work Units.
- Validity constraints.

### 4.2 Scoped authorization

A grant must be no broader than the authority explicitly issued.

For example, authorization to modify one service does not imply authorization to modify every file in the repository.

### 4.3 Operation scope

The grant must identify which operations are permitted.

Relevant operations may include:

- `create_branch`
- `implement`
- `run_tests`
- `stage`
- `commit`
- `push`
- `create_pr`
- `merge`

The exact operation vocabulary is governed by the versioned contracts.

### 4.4 Path scope

The grant may define allowed and protected paths.

Protected paths take precedence over allowed paths.

### 4.5 Work Unit scope

Authorization may apply to one or more identified Work Units.

A grant for one Work Unit must not automatically authorize unrelated Work Units.

### 4.6 Validity

Grants must support validation of relevant constraints such as:

- Expiration.
- Revocation.
- Plan revision.
- Repository baseline.
- Workspace applicability.
- Operation scope.

### 4.7 No implicit expansion

A grant must not expand automatically because an AI agent discovers additional work.

Material scope changes require authorization reassessment.

---

## 5. Execution Envelopes

An Execution Envelope defines the bounded execution requested for a task or Work Unit.

### 5.1 Purpose

The envelope connects the approved engineering plan to the deterministic execution controller.

### 5.2 Required binding

An envelope must identify:

- Execution identity.
- Task identity.
- Plan revision.
- Work Unit identity or applicable scope.
- Context Package identity.
- Approval Grant reference.
- Repository identity.
- Branch and baseline.
- Workspace observation.
- Requested operations.
- Allowed execution scope.
- Resource budgets.
- Verification requirements.
- Delivery preparation policy.

### 5.3 Envelope validation

The execution controller must validate the envelope against:

- The active task.
- The approved plan revision.
- The immutable Context Package.
- The trusted Approval Grant.
- Repository policy.
- Current repository and workspace observations.

### 5.4 No authority creation

An Execution Envelope is a request for controlled execution.

It does not create authority.

### 5.5 Scope intersection

The effective execution permissions must be no broader than the intersection of:

1. Trusted authorization.
2. Repository policy.
3. Task and plan scope.
4. Execution Envelope scope.
5. Guarded tool capabilities.

If any layer denies an operation, the operation must not proceed.

### 5.6 Read-only execution

The architecture must support read-only investigations without requiring commit preparation.

A known draft-contract issue exists where the execution schema requires `delivery.prepare_commit=true`.

That requirement must be corrected through a reviewed, versioned contract change before read-only Explore workflows are considered fully supported.

---

## 6. Guarded Tool Architecture

Restricted operations must pass through deterministic guarded adapters.

### 6.1 Core rule

The AI must not be able to bypass execution policy by directly invoking an unrestricted equivalent of a guarded operation.

### 6.2 Guarded operation categories

The initial architecture may include adapters for:

- Filesystem inspection.
- Filesystem modification.
- Git inspection.
- Git mutation.
- Test execution.
- Build execution.
- External process execution.
- GitHub read operations.
- GitHub publication operations.

### 6.3 Tool mediation

Each guarded operation must validate the relevant authorization and runtime constraints before execution.

### 6.4 Filesystem writes

Guarded filesystem writes must enforce ADR-004, including:

- Repository confinement.
- Allowed-path validation.
- Protected-path precedence.
- Expected-content verification.
- Concurrent modification detection.
- Safe creation and replacement.

### 6.5 Git operations

Git mutation must be separately authorized.

The engine must distinguish:

- Read-only inspection.
- Branch creation.
- Synchronization.
- Staging.
- Commit.
- Push.
- PR creation.
- Merge.

Permission for one operation does not imply permission for another.

### 6.6 Process execution

Arbitrary process execution is a significant security boundary.

A test command or build command may execute arbitrary code through scripts, plugins, hooks, or subprocesses.

Therefore, a command being labeled `run_tests` does not make it harmless.

The controller must enforce the applicable command policy, working directory, environment, resource limits, and authorization.

### 6.7 Network operations

Network access must be controlled according to task requirements and applicable policy.

Read-only intent does not guarantee absence of side effects in arbitrary external systems.

### 6.8 Tool failure

Guarded adapters must return structured outcomes.

Failures must not silently expand permissions or trigger unrestricted fallback operations.

---

## 7. Execution Isolation

The deterministic controller must enforce the boundary between reasoning and execution.

### 7.1 Enforcement requirement

Guarded adapters are effective only if the AI cannot reach equivalent unrestricted capabilities.

### 7.2 Execution environment

The implementation must define an execution environment appropriate to its threat model.

Possible mechanisms include:

- Restricted process capabilities.
- Filesystem sandboxing.
- Container isolation.
- Explicit tool allowlists.
- Controlled credentials.
- Limited network access.

### 7.3 No assumed sandbox

A Python wrapper around filesystem operations is not, by itself, a complete security sandbox.

If unrestricted shell access remains available to the agent, guarded filesystem checks alone cannot guarantee confinement.

### 7.4 Initial implementation

The first vertical slice may establish policy enforcement within the supported tool interface.

It must document the actual enforcement boundary and avoid claiming stronger isolation than has been demonstrated.

### 7.5 Escalation

Operations requiring capabilities beyond the supported isolation model must be denied or escalated for explicit handling.

---

## 8. Execution Budgets

AEW must enforce resource budgets during controlled execution.

### 8.1 Purpose

Budgets prevent uncontrolled execution, excessive retries, unbounded investigation, and unnecessary resource consumption.

### 8.2 Budget dimensions

The initial design may support:

- Wall-clock duration.
- Tool invocation count.
- Execution steps.
- Retry attempts.
- Output volume.
- Context expansion count.
- Files modified.
- Command-specific limits.

Additional dimensions may be introduced when justified.

### 8.3 Progress-aware budgeting

Budgets must account for useful progress rather than relying exclusively on a rigid number of steps.

For example, a long-running integration test may legitimately require more time than a localized source inspection.

### 8.4 Hard limits

Progress awareness must not eliminate hard safety limits.

A process making apparent progress cannot continue indefinitely.

### 8.5 Budget exhaustion

When a required budget is exhausted, AEW must suspend or terminate the affected execution safely.

It must not silently increase the limit.

### 8.6 Budget extensions

Extensions require an appropriate trusted authorization or policy decision.

An AI-generated justification does not independently authorize additional resources.

### 8.7 Budget accounting

Budget consumption should be recorded in execution state.

The system must not reset consumed budgets merely because a checkpoint is resumed.

---

## 9. Execution State Machine

Controlled execution requires explicit lifecycle states.

### 9.1 Suggested states

The logical model should support:

| State | Meaning |
|---|---|
| Prepared | Envelope assembled but not executing |
| Validating | Authorization and runtime checks in progress |
| Ready | Required checks satisfied |
| Running | Controlled operations in progress |
| Suspended | Execution paused pending reconciliation or authorization |
| Completed | Authorized operations finished |
| Failed | Execution ended unsuccessfully |
| Cancelled | Execution intentionally terminated |

The exact serialized vocabulary may differ.

### 9.2 State transitions

Transitions must be validated.

For example:

```text id="r4f67w"
Prepared
    |
    v
Validating
    |
    +---- invalid ----> Failed
    |
    v
Ready
    |
    v
Running
    |
    +---- conflict ----> Suspended
    |
    +---- budget ------> Suspended
    |
    +---- error -------> Failed
    |
    +---- success -----> Completed
```

A suspended execution may return to validation before resumption.

### 9.3 Invalid transitions

The engine must reject invalid state transitions.

An execution must not move directly from an unvalidated state to unrestricted operation.

### 9.4 Completion semantics

Completed means the authorized execution operations finished according to the controller's criteria.

It does not automatically mean:

- Tests passed.
- The feature is correct.
- The task is accepted.
- A commit was created.
- Changes were published.

These outcomes require separate evidence and state.

---

## 10. Durable Checkpoints

Long-running work must support safe interruption and resumption.

### 10.1 Checkpoint purpose

A checkpoint records enough execution state to support controlled continuation.

### 10.2 Required checkpoint information

A checkpoint should retain:

- Execution identity.
- Task and Work Unit identity.
- Plan revision.
- Context Package identity.
- Approval Grant reference.
- Repository and workspace observations.
- Completed operations.
- Pending operations.
- Budget consumption.
- Verification evidence.
- Relevant errors and uncertainties.

### 10.3 Durability

Checkpoints must survive process interruption according to the supported persistence guarantees.

### 10.4 Atomicity

Checkpoint publication must not leave an ambiguous partially committed execution state.

### 10.5 Resumption

Before resuming, AEW must revalidate:

- Trusted authorization.
- Grant expiration and revocation.
- Plan revision.
- Context Package integrity and applicability.
- Repository identity.
- Branch and baseline.
- Workspace consistency.
- Remaining budgets.
- Pending operation scope.

### 10.6 No unconditional replay

A checkpoint is not permission to replay operations without validation.

### 10.7 Idempotency

Operations should be designed for safe retry where practical.

For operations with non-idempotent external effects, AEW must preserve enough information to avoid accidental duplicate execution.

### 10.8 Unknown outcomes

If an interrupted external operation may have completed but its result is unknown, AEW must reconcile the outcome before retrying.

---

## 11. Workspace Consistency

ADR-004 establishes the workspace protection model.

Controlled execution must enforce it.

### 11.1 Pre-execution observation

The controller must establish the expected repository and workspace state.

### 11.2 Pre-write checks

Before modifying a file, the guarded adapter must verify its expected identity.

### 11.3 Concurrent changes

Unexpected changes affecting the operation must cause rejection or suspension.

### 11.4 Unrelated modifications

The engine must preserve unrelated workspace changes.

### 11.5 Scope expansion

Newly discovered files outside the authorized scope require reassessment.

### 11.6 Checkpoint recovery

Workspace assumptions must be revalidated after interruption.

---

## 12. Context Package Binding

ADR-009 establishes immutable Context Packages.

### 12.1 Explicit binding

An execution must identify the Context Package supporting its plan.

### 12.2 Integrity validation

The controller must verify package integrity.

### 12.3 Revision compatibility

The package must remain applicable to the execution's repository observation.

### 12.4 Context expansion

If additional context is required, AEW may create a new Context Package.

Execution must not silently switch packages.

### 12.5 Rebinding

Rebinding requires an explicit transition and relevant plan, authorization, and workspace validation.

---

## 13. Plan and Work Unit Binding

ADR-012 governs adaptive planning.

ADR-011 governs Work Units.

### 13.1 Plan revision

Execution must be associated with an identified plan revision.

### 13.2 Work Unit identity

Execution scope must identify the Work Unit or bounded operation set.

### 13.3 Material changes

Material changes to scope, dependencies, protected paths, or required operations may invalidate existing authorization.

### 13.4 Sequential checkpoints

Work Units should support human review at meaningful boundaries.

### 13.5 No implicit continuation

Completing one Work Unit does not automatically authorize unrelated or newly expanded work.

---

## 14. Verification Evidence

Execution must distinguish attempted verification from observed results.

### 14.1 Evidence categories

Verification evidence may include:

- Test command.
- Exit status.
- Relevant output.
- Build result.
- Static analysis result.
- Changed-file summary.
- Diff inspection.
- Manual verification notes.

### 14.2 Execution versus success

A test command being invoked does not establish that tests passed.

### 14.3 Missing verification

Unavailable or skipped verification must be reported explicitly.

### 14.4 Evidence integrity

Verification records should retain sufficient identity and context to establish which repository state was tested.

### 14.5 Failure handling

Verification failure must not automatically authorize unrelated changes or broader execution.

### 14.6 Delivery readiness

Delivery preparation must reflect actual verification outcomes.

A completed implementation with failing tests must not be reported as fully verified.

---

## 15. Auditability

Controlled execution must produce traceable records.

### 15.1 Audit requirements

Records should identify:

- Execution identity.
- Authorization reference.
- Requested operation.
- Effective scope.
- Validation outcome.
- Relevant repository observation.
- Operation result.
- Budget consumption.
- Checkpoint transitions.
- Verification evidence.

### 15.2 Sensitive information

Audit records must not unnecessarily expose:

- Credentials.
- Tokens.
- Private keys.
- Confidential file contents.
- Sensitive environment variables.

### 15.3 Audit limitations

An application log is not automatically tamper-proof.

The implementation must not claim tamper resistance without an appropriate storage and trust model.

### 15.4 Historical traceability

Retained execution records should support reconstruction of why a particular operation was allowed or denied.

---

## 16. Architectural Invariants

The following invariants are mandatory.

### INV-001 — AI reasoning is not authorization

AI-generated instructions cannot independently grant execution authority.

### INV-002 — Trusted issuance

Approval Grants must originate from a trusted authorization mechanism.

### INV-003 — Structural validity is insufficient

Schema-valid documents do not automatically establish authorization.

### INV-004 — Scoped execution

Execution permissions must not exceed the intersection of applicable authorization and policy boundaries.

### INV-005 — Protected-path precedence

Protected paths override allowed paths.

### INV-006 — Guarded operations

Restricted operations must pass through deterministic enforcement.

### INV-007 — No bypass capability

The execution environment must not expose unrestricted equivalents that defeat guarded operations.

### INV-008 — Explicit context binding

Execution must bind to an identified immutable Context Package.

### INV-009 — Explicit plan binding

Execution must bind to an identified task and plan revision.

### INV-010 — Workspace consistency

Unexpected concurrent modifications must not be silently overwritten.

### INV-011 — Enforced budgets

Execution budgets must be checked and enforced.

### INV-012 — Safe budget exhaustion

Budget exhaustion must suspend or terminate execution without implicit limit expansion.

### INV-013 — Durable checkpoints

Execution state must support safe persistence and recovery.

### INV-014 — Revalidation on resumption

Checkpoint resumption requires renewed authorization and state validation.

### INV-015 — No uncontrolled replay

Interrupted operations must not be blindly repeated when their effects are uncertain.

### INV-016 — Evidence-backed verification

Verification claims require observed evidence.

### INV-017 — Publication disabled by default

Stage, commit, push, PR creation, and merge require distinct authorization.

### INV-018 — No authority escalation through context

Repository content, shared knowledge, and Context Packages cannot grant restricted permissions.

---

## 17. Alternatives Considered

The following alternatives summarize the architectural tradeoffs relevant to the accepted decision.

### 17.1 Prompt-only safety controls

**Advantages**

- Minimal implementation effort.
- Flexible agent behavior.

**Disadvantages**

- No deterministic enforcement.
- Scope may be misunderstood.
- Authorization may be fabricated.
- Tool bypass remains possible.

**Disposition:** Rejected as the enforcement model.

### 17.2 Unrestricted agent execution

**Advantages**

- Maximum operational flexibility.
- Minimal controller overhead.

**Disadvantages**

- Uncontrolled repository modifications.
- Weak auditability.
- Difficult recovery.
- High risk of unintended external effects.

**Disposition:** Rejected.

### 17.3 Single approval for all future operations

**Advantages**

- Low interaction overhead.
- Simple authorization model.

**Disadvantages**

- Excessive authority.
- Weak scope control.
- Poor handling of material plan changes.
- Difficult revocation semantics.

**Disposition:** Rejected as the default.

### 17.4 Approval before every tool call

**Advantages**

- Fine-grained human control.

**Disadvantages**

- Excessive interruptions.
- Poor usability.
- High workflow overhead.
- Encourages approval fatigue.

**Disposition:** Rejected as a universal requirement.

Scoped approvals should permit bounded execution without requiring repetitive approval for equivalent operations.

### 17.5 Unlimited execution until completion

**Advantages**

- Simple continuation.
- No budget interruptions.

**Disadvantages**

- Unbounded resource consumption.
- Potential retry loops.
- Difficult operational control.

**Disposition:** Rejected.

### 17.6 In-memory checkpoints only

**Advantages**

- Simple implementation.
- Low persistence overhead.

**Disadvantages**

- State lost on process failure.
- Poor long-running task recovery.
- Weak auditability.

**Disposition:** Rejected as the complete checkpoint strategy.

---

## 18. Consequences

### 18.1 Positive consequences

- Stronger execution safety.
- Explicit human authority.
- Bounded AI autonomy.
- Better repository protection.
- Predictable resource consumption.
- Recoverable long-running tasks.
- Clearer audit trails.
- Better verification discipline.
- Safer multi-session workflows.
- Reduced risk of unauthorized publication.

### 18.2 Costs

- Authorization infrastructure.
- Execution controller complexity.
- Guarded adapter implementation.
- Checkpoint persistence.
- Resource accounting.
- Runtime validation.
- Isolation requirements.
- More extensive negative testing.

### 18.3 Risks

**False authorization**

A fabricated or stale grant may be accepted.

Mitigation: Trusted issuance, validity checks, and revocation handling.

**Tool bypass**

An agent may access unrestricted execution capabilities.

Mitigation: Enforce capability isolation at the execution environment boundary.

**Time-of-check/time-of-use races**

Repository state may change after validation.

Mitigation: Guarded operations and immediate state checks.

**Checkpoint inconsistency**

A partially persisted checkpoint may misrepresent completed work.

Mitigation: Atomic checkpoint publication and operation reconciliation.

**Approval fatigue**

Excessive authorization prompts may undermine usability.

Mitigation: Scoped, event-driven approvals.

**Budget misuse**

Rigid or overly permissive budgets may either interrupt useful work or allow runaway execution.

Mitigation: Progress-aware accounting with hard limits.

---

## 19. Implementation Guidance

### 19.1 Initial milestone

Controlled execution belongs to M5.

The implementation must not begin before the prerequisite contracts, Context Packages, and authorization model are sufficiently established.

### 19.2 Existing contracts

The initial contracts are:

- `contracts/approval.schema.json`
- `contracts/execution.schema.json`

Codex must validate these contracts against the accepted architectural invariants.

### 19.3 Minimum viable controller

The first controlled execution slice should support:

- Trusted grant validation.
- Envelope validation.
- Repository and workspace binding.
- Context Package integrity verification.
- Allowed-operation enforcement.
- Allowed-path enforcement.
- Protected-path precedence.
- Guarded filesystem modifications.
- Execution budgets.
- Structured operation outcomes.
- Durable checkpoints.
- Safe suspension and resumption.

### 19.4 Suggested logical interfaces

Possible operations include:

```text id="jj2d7x"
validate_trusted_grant(grant, authority_context)

validate_execution_envelope(envelope, grant)

calculate_effective_permissions(envelope, grant, policy)

authorize_operation(execution, operation, target)

execute_guarded_operation(execution, operation)

record_execution_checkpoint(execution)

revalidate_execution_resume(checkpoint)

collect_verification_evidence(execution)
```

These are conceptual operations, not mandated Python signatures.

### 19.5 Authorization implementation

The initial implementation must define how trusted approval issuance is established.

The system must not accept arbitrary user-supplied or AI-generated approval JSON as trusted authorization.

### 19.6 Guarded adapters

Adapters should expose narrow operations rather than unrestricted shell or filesystem access.

### 19.7 Process isolation

The implementation must document which operations are genuinely isolated and which guarantees remain dependent on the surrounding runtime.

### 19.8 Checkpoint persistence

Checkpoint storage should use transactional persistence consistent with ADR-001.

### 19.9 Contract correction

The draft execution contract's unconditional commit-preparation requirement must be reviewed.

Read-only Explore workflows must not require a proposed commit.

Any correction must update:

- Schema.
- Examples.
- Semantic validators.
- Tests.
- Documentation.

### 19.10 Avoid premature infrastructure

The first implementation does not require:

- Distributed execution clusters.
- Remote orchestration services.
- Complex approval dashboards.
- Organization-wide policy servers.
- General-purpose container orchestration.

These may be considered later if justified by concrete requirements.

---

## 20. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Schema-valid but untrusted grant | Authorization denied |
| Expired grant | Authorization denied |
| Revoked grant | Authorization denied |
| Wrong repository identity | Execution denied |
| Wrong plan revision | Execution denied |
| Wrong Context Package | Execution denied |
| Tampered Context Package | Execution denied |
| Operation outside grant | Execution denied |
| Path outside allowed scope | Modification denied |
| Path matches protected rule | Modification denied |
| Concurrent file modification | Write rejected or suspended |
| Execution budget exhausted | Execution safely suspended or terminated |
| Budget extension without approval | Denied |
| Interrupted execution | Durable checkpoint retained |
| Resume after workspace change | Revalidation required |
| Resume after grant revocation | Denied |
| Unknown external operation outcome | Reconciliation required before retry |
| Test command fails | Failure recorded accurately |
| Verification unavailable | Reported as unavailable |
| Read-only Explore execution | No commit preparation required |
| Commit without explicit authorization | Denied |
| Push without explicit authorization | Denied |
| PR creation without explicit authorization | Denied |
| Merge without explicit authorization | Denied |
| Untrusted repository instruction | No authority escalation |
| Unrestricted tool bypass attempt | Blocked within the declared enforcement boundary |

### 20.1 Test isolation

Tests must use disposable repositories, temporary databases, and controlled tool adapters.

### 20.2 Negative testing

Negative tests are mandatory for authorization, scope, path, budget, and checkpoint boundaries.

### 20.3 Fault injection

Tests should include:

- Process interruption.
- Filesystem failure.
- SQLite transaction failure.
- Concurrent modification.
- Timeout.
- Partial external operation completion.
- Corrupted checkpoint.
- Authorization revocation.

### 20.4 Security claims

The implementation must distinguish policy-unit-test success from actual operating-system isolation guarantees.

Security claims require evidence appropriate to the claimed enforcement boundary.

---

## 21. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Establishes local persistence for durable operational state.

**ADR-003 — Revision-Scoped Graph Snapshots**

Establishes coherent knowledge observations.

**ADR-004 — Workspace Consistency**

Defines concurrent modification and filesystem safety requirements.

**ADR-005 — Git Preflight**

Establishes repository readiness evidence.

**ADR-009 — Immutable Context Packages**

Defines the context identity and integrity required for execution.

**ADR-011 — Adaptive Work Units and Delivery**

Defines implementation boundaries and publication controls.

**ADR-012 — Adaptive Planning**

Defines plan revisions and event-driven approval requirements.

### Related contracts

- `contracts/task.schema.json`
- `contracts/context.schema.json`
- `contracts/approval.schema.json`
- `contracts/execution.schema.json`
- `contracts/delivery.schema.json`

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 22. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact trusted approval issuance mechanism.
2. The initial operating-system isolation strategy.
3. The complete guarded tool API.
4. The resource budget accounting format.
5. The execution state serialization model.
6. The checkpoint schema and retention policy.
7. The authorization revocation propagation mechanism.
8. The policy for reconciling uncertain external operation outcomes.
9. The supported command execution environments.
10. The initial network access policy.
11. The exact process for rebinding execution to a new Context Package.
12. The mechanism for coordinating concurrent AEW execution processes.

These decisions must be resolved before implementation claims the corresponding safety guarantees.

They must preserve the architectural invariants established above.

---

## 23. Acceptance and Compliance

ADR-010 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Restricted operations require trusted authorization.
- Schema-valid approval documents cannot independently grant authority.
- Execution Envelopes cannot exceed approved scope.
- Guarded operations enforce path and operation boundaries.
- The execution environment prevents bypass within its declared threat model.
- Context Package and plan identity are validated.
- Workspace consistency is enforced.
- Resource budgets are enforced.
- Checkpoints survive interruption.
- Resumption revalidates authorization and state.
- Verification claims are evidence-backed.
- Git publication operations remain disabled without explicit authorization.

Compliance requires observed verification evidence.

The existence of this ADR does not establish that these capabilities have been implemented.

---

## 24. Decision Summary

AEW uses trusted Approval Grants and scoped Execution Envelopes to control engineering operations.

A deterministic execution controller validates authorization, repository state, Context Package identity, execution scope, and resource budgets before allowing guarded operations.

Execution supports safe suspension, durable checkpoints, and revalidation before resumption.

Verification claims require observed evidence.

AI-generated plans, Context Packages, configuration, and schema-valid approval documents cannot independently create execution authority.

**The AI determines what may be useful to do. The trusted execution system determines what is permitted to happen.**