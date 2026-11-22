# ADR-011 — Adaptive Work Units and Controlled Delivery

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Work Unit decomposition, implementation boundaries, verification, commit preparation, human review checkpoints, and controlled Git delivery  
**Related milestones:** M4 — Adaptive Planning and Work Units; M5 — Controlled Execution; M6 — Verification and Delivery Preparation

---

## 1. Context

The Adaptive Engineering Workbench (AEW) supports engineering tasks ranging from small bug fixes to complex, multi-stage implementations.

A small change may require modifying one function and updating a test.

A larger task may involve:

- Introducing a new contract.
- Implementing a service.
- Updating persistence.
- Migrating existing behavior.
- Adding integration tests.
- Updating documentation.
- Preparing deployment changes.

Treating every task as one indivisible operation creates several problems.

Large changes become difficult to review, verify, recover, and reason about.

Conversely, dividing every task into tiny implementation steps introduces excessive overhead and produces fragmented commits with little engineering meaning.

AEW therefore requires an adaptive unit of work that represents a coherent engineering change.

Each unit should be independently understandable, reviewable, and verifiable to the extent appropriate for its purpose.

AEW must also distinguish implementation progress from Git delivery.

An AI agent may complete a Work Unit and prepare a commit proposal without being authorized to stage files, create a commit, push a branch, or open a pull request.

---

## 2. Decision

AEW will use **adaptive Work Units as the primary implementation and delivery boundaries**.

A Work Unit represents a meaningful, bounded engineering change within an approved task plan.

The default delivery strategy is:

**One proposed Git commit per meaningful Work Unit.**

Each Work Unit should produce:

- A defined objective.
- An explicit implementation scope.
- Relevant dependencies.
- Acceptance criteria.
- Verification requirements.
- A change summary.
- Verification evidence.
- A proposed commit title.
- A proposed commit body.
- A completion status.

Actual Git operations remain separately authorized.

### 2.1 Adaptive decomposition

Work Units must be sized according to engineering coherence, not an arbitrary number of files or implementation steps.

A small task may contain one Work Unit.

A complex task may contain several Work Units.

### 2.2 Human checkpoints

AEW will support sequential human review checkpoints between meaningful Work Units.

The engineer may inspect the result, approve continuation, request changes, or revise the remaining plan.

### 2.3 Publication boundary

By default, AEW must not automatically:

- Stage changes.
- Create commits.
- Push branches.
- Create pull requests.
- Merge pull requests.

These operations require explicit authorization under ADR-010.

### 2.4 Delivery preparation

AEW may prepare proposed commit messages, change summaries, verification reports, and pull request descriptions without performing the corresponding Git publication operations.

---

## 3. Work Unit Definition

A Work Unit is a bounded engineering objective with an identifiable completion condition.

### 3.1 Required concepts

Each Work Unit must identify:

1. Work Unit ID.
2. Parent task.
3. Applicable plan revision.
4. Objective.
5. Intended change scope.
6. Dependencies.
7. Acceptance criteria.
8. Verification requirements.
9. Relevant authorization boundaries.
10. Execution and delivery status.

### 3.2 Work Unit identity

A Work Unit must have a stable identity within its task and plan context.

A material revision may require a new Work Unit identity or an explicit version relationship.

### 3.3 Engineering coherence

A Work Unit should represent a change that can be explained as one meaningful engineering outcome.

Examples include:

- Add a validated API contract.
- Implement a persistence adapter.
- Correct a localized defect and add regression coverage.
- Introduce a compatibility layer.
- Migrate one bounded integration path.
- Add an isolated verification capability.

### 3.4 Avoid artificial fragmentation

A Work Unit should not be split merely because implementation involves several files.

For example, correcting a bug and adding its regression test normally belong in the same Work Unit.

### 3.5 Avoid oversized units

A Work Unit should not combine unrelated engineering objectives simply to reduce the number of checkpoints.

A unit containing multiple independent architectural changes should be reconsidered.

---

## 4. Adaptive Work Unit Sizing

Work Unit size depends on:

- Task complexity.
- Architectural boundaries.
- Risk.
- Dependencies.
- Verification cost.
- Reviewability.
- Reversibility.
- Existing project conventions.
- Uncertainty.

### 4.1 Small tasks

A localized bug fix may use one Work Unit.

```text
Task: Correct null customer response

WU-001:
    Correct null handling.
    Add regression test.
    Verify affected tests.
    Prepare one commit proposal.
```

### 4.2 Medium tasks

A feature may use several units.

```text
Task: Add customer export

WU-001:
    Define export contract.

WU-002:
    Implement export service.

WU-003:
    Add integration verification.
```

Each unit must have a meaningful engineering boundary.

### 4.3 Large tasks

A modernization effort may use units corresponding to migration capabilities or compatibility boundaries.

For example:

```text
Task: Introduce modern customer gateway

WU-001:
    Characterize existing integration contract.

WU-002:
    Implement compatibility adapter.

WU-003:
    Add contract verification.

WU-004:
    Migrate one consumer.

WU-005:
    Verify backward compatibility.
```

Read-only investigation units do not necessarily require a commit proposal.

### 4.4 No fixed file-count rule

AEW must not impose a universal limit such as one file per Work Unit or five files per commit.

Engineering coherence is the governing criterion.

---

## 5. Work Unit Dependencies

Work Units may depend on one another.

### 5.1 Dependency types

Dependencies may include:

- Contract dependencies.
- Implementation dependencies.
- Verification prerequisites.
- Repository baseline dependencies.
- External approvals.
- Environment availability.

### 5.2 Dependency representation

Dependencies must be explicit when they affect execution order or correctness.

### 5.3 Sequential execution

The initial implementation may execute Work Units sequentially.

Parallel execution is not required for the first vertical slice.

### 5.4 Parallel execution

Future implementations may support independent Work Units executing concurrently.

However, concurrency requires compatible:

- Repository observations.
- Workspace scopes.
- Authorization.
- File ownership boundaries.
- Integration strategy.

### 5.5 Dependency changes

If a Work Unit discovers an unexpected dependency, AEW must reassess the remaining plan.

It must not silently expand the Work Unit beyond its approved scope.

---

## 6. Work Unit Lifecycle

The logical Work Unit lifecycle includes:

| State | Meaning |
|---|---|
| Proposed | Work Unit identified during planning |
| Ready | Dependencies and required preconditions satisfied |
| In progress | Authorized work underway |
| Suspended | Work paused pending reconciliation or approval |
| Implemented | Intended modifications completed |
| Verified | Required verification completed successfully |
| Review pending | Awaiting human review or acceptance |
| Accepted | Engineer or applicable policy accepts the Work Unit result |
| Failed | Work Unit could not satisfy its required outcome |
| Cancelled | Work Unit intentionally discontinued |

The exact serialized vocabulary may differ.

### 6.1 Implementation versus verification

A Work Unit may be implemented without being verified.

For example, source changes may be complete while integration tests remain unavailable.

### 6.2 Verification versus acceptance

A Work Unit may pass tests but still require engineering review.

Test success does not automatically establish acceptance.

### 6.3 Acceptance versus publication

An accepted Work Unit does not automatically imply that a Git commit or push has occurred.

### 6.4 Publication state

Git publication should be tracked separately from Work Unit engineering status.

This avoids conflating code readiness with repository mutation.

---

## 7. Work Unit Execution

ADR-010 governs controlled execution.

### 7.1 Execution binding

Each controlled Work Unit execution must identify:

- Task.
- Plan revision.
- Work Unit.
- Context Package.
- Approval Grant.
- Execution Envelope.
- Repository observation.
- Authorized operations.

### 7.2 Scope enforcement

Execution must remain within the Work Unit's authorized boundaries.

### 7.3 Protected paths

Protected-path rules take precedence over allowed paths.

### 7.4 Concurrent modifications

ADR-004's file-level consistency checks must be enforced.

### 7.5 Scope changes

Newly discovered implementation requirements may justify revising the Work Unit.

Material changes require plan and authorization reassessment.

### 7.6 Checkpoints

Long-running Work Units must support durable execution checkpoints.

### 7.7 Recovery

Resumption requires renewed validation of repository, context, authorization, and workspace assumptions.

---

## 8. Verification Requirements

Every implementation Work Unit must define proportionate verification expectations.

### 8.1 Verification categories

Verification may include:

- Unit tests.
- Integration tests.
- Contract validation.
- Static analysis.
- Type checking.
- Build verification.
- Regression tests.
- Security checks.
- Manual review.
- Runtime validation.

### 8.2 Verification selection

The required checks depend on:

- Change scope.
- Architectural impact.
- Risk.
- Existing test infrastructure.
- Acceptance criteria.
- Project conventions.

### 8.3 Evidence

Verification records must identify:

- What was executed.
- Which repository state was tested.
- The observed outcome.
- Relevant failures.
- Skipped or unavailable checks.
- Remaining limitations.

### 8.4 No false success

A test command being discovered does not mean it was executed.

A command being executed does not mean it passed.

A passing test does not prove every requirement is satisfied.

### 8.5 Partial verification

If required verification cannot be completed, the Work Unit must retain an explicit limitation.

It must not be marked fully verified.

### 8.6 Verification failure

Failure may trigger correction within the authorized scope.

It must not automatically authorize broader implementation or unrelated refactoring.

---

## 9. Change Boundaries

A Work Unit must identify which changes belong to it.

### 9.1 Intended files

The Work Unit should identify expected files or repository regions when practical.

### 9.2 Actual changes

After implementation, AEW must inspect the actual diff.

### 9.3 Scope reconciliation

The actual diff must be compared against the authorized Work Unit scope.

### 9.4 Unrelated changes

Unrelated staged, unstaged, or untracked changes must remain preserved.

### 9.5 Unexpected modifications

Unexpected changes must be investigated before delivery preparation.

### 9.6 Generated files

Generated artifacts may belong to a Work Unit when required.

Their inclusion must be deliberate and consistent with repository conventions.

### 9.7 Cross-unit changes

A file may be modified by multiple sequential Work Units.

AEW must distinguish the changes attributable to each unit.

If the resulting changes cannot be safely separated, the Work Unit boundaries or delivery strategy must be reconsidered.

---

## 10. Proposed Commit Model

The default strategy is one proposed commit per meaningful implementation Work Unit.

### 10.1 Commit proposal

A proposal should contain:

- Work Unit identity.
- Proposed commit title.
- Proposed commit body.
- Intended change boundary.
- Verification summary.
- Relevant limitations.

### 10.2 Commit title

The title should describe the engineering outcome.

It should follow repository conventions when available.

Example:

```text
fix(customer): handle missing repository results
```

### 10.3 Commit body

The body should explain:

- What changed.
- Why the change was necessary.
- Important compatibility considerations.
- Relevant verification.

Example:

```text
Normalize missing customer repository results before
response mapping.

Add regression coverage for absent customer records
and preserve existing error propagation behavior.

Verification:
- CustomerServiceTest: passed
- CustomerControllerTest: passed
```

### 10.4 Proposal versus execution

Generating a commit message does not authorize staging or committing.

### 10.5 Read-only units

Read-only investigation or Explore Work Units do not require a proposed commit when no repository changes are intended.

### 10.6 Exceptions

A Work Unit may legitimately require a different delivery arrangement.

Exceptions must be explicit and justified.

The one-commit-per-unit rule is a default engineering strategy, not an inflexible filesystem or Git invariant.

---

## 11. Git Staging

Staging is a separately authorized operation.

### 11.1 Default policy

AEW must not stage files automatically.

### 11.2 Authorized staging

When staging is authorized, AEW must stage only the intended Work Unit changes.

### 11.3 Existing index content

Pre-existing staged changes must not be assumed to belong to the Work Unit.

### 11.4 Partial-file changes

When a file contains both Work Unit changes and unrelated modifications, AEW must not stage the entire file indiscriminately.

The implementation may require patch-level staging or human reconciliation.

### 11.5 Staging verification

Before commit execution, AEW must inspect the staged content and verify its relationship to the approved change boundary.

### 11.6 Broad staging

Commands such as `git add -A` must not be used as an unrestricted shortcut in a shared dirty workspace.

Any staging strategy must preserve unrelated changes.

---

## 12. Commit Execution

Commit execution requires distinct authorization.

### 12.1 Preconditions

Before creating a commit, AEW must validate:

- Trusted authorization.
- Work Unit identity.
- Plan revision.
- Repository and branch identity.
- Expected baseline.
- Staged change boundary.
- Verification requirements.
- Repository policy.

### 12.2 Existing staged changes

Unrelated staged content must not be silently included.

### 12.3 Commit hooks

Git hooks may execute arbitrary commands.

The execution controller must account for hook behavior within its declared security and authorization model.

### 12.4 Commit failure

A failed commit must be reported accurately.

AEW must not silently retry using broader permissions.

### 12.5 Sequential checkpoints

After a meaningful Work Unit commit, AEW should support a review checkpoint before continuing to the next unit.

### 12.6 No automatic publication

A local commit does not authorize pushing to a remote.

---

## 13. Push and Pull Request Preparation

Push and PR creation are separate operations.

### 13.1 Push

Pushing requires explicit authorization and relevant remote-state validation.

### 13.2 Pull request preparation

AEW may draft:

- PR title.
- PR description.
- Change summary.
- Verification summary.
- Known risks.
- Relevant issue references.
- Work Unit overview.

### 13.3 Pull request creation

Creating a PR requires explicit authorization.

### 13.4 Merge

Merging requires separate authorization and applicable repository policy checks.

### 13.5 No implicit operation chaining

Authorization to commit does not imply authorization to push.

Authorization to push does not imply authorization to create a PR.

Authorization to create a PR does not imply authorization to merge.

### 13.6 Remote freshness

Relevant remote state must be revalidated before publication.

A successful preflight from an earlier point in time is not permanent clearance.

---

## 14. Delivery Package

AEW should produce a structured delivery record for completed Work Units or tasks.

### 14.1 Purpose

The delivery record communicates what was accomplished and what remains unresolved.

### 14.2 Required information

A delivery record should identify:

- Task identity.
- Plan revision.
- Work Units.
- Implementation summary.
- Changed-file boundaries.
- Verification evidence.
- Proposed commits.
- Known limitations.
- Publication status.
- Recommended next action.

### 14.3 Existing contract

The initial contract is:

`contracts/delivery.schema.json`

The schema must be reviewed against the accepted ADR before implementation is considered complete.

### 14.4 Evidence

The delivery record must distinguish:

- Proposed operations.
- Executed operations.
- Verified outcomes.
- Unavailable checks.

### 14.5 No fabricated delivery state

AEW must not report a commit, push, PR, or merge as completed unless the corresponding operation actually occurred and its outcome was verified.

---

## 15. Human Review Checkpoints

AEW supports meaningful human review between Work Units.

### 15.1 Review purpose

Review checkpoints allow the engineer to:

- Inspect implementation.
- Review verification.
- Confirm architectural alignment.
- Approve continuation.
- Request corrections.
- Reassess remaining work.
- Adjust priorities.

### 15.2 Event-driven review

Review should occur at meaningful engineering boundaries.

It should not require approval after every trivial tool call.

### 15.3 Sequential progression

The default workflow processes Work Units sequentially with review checkpoints where required by the plan or authorization policy.

### 15.4 Review outcomes

A checkpoint may result in:

- Acceptance.
- Requested changes.
- Plan revision.
- Scope reduction.
- Additional investigation.
- Suspension.
- Cancellation.

### 15.5 Authorization independence

Accepting a Work Unit result does not automatically authorize Git publication.

The approval mechanism must preserve that distinction.

---

## 16. Adaptive Planning Integration

ADR-012 governs planning profiles and approval events.

### 16.1 Quick tasks

A Quick task may contain one Work Unit with minimal planning overhead.

### 16.2 Standard tasks

A Standard task may contain several units with explicit dependencies and verification.

### 16.3 Deep tasks

A Deep task may require architectural checkpoints, contract-first sequencing, and more extensive verification.

### 16.4 Explore tasks

Explore tasks may produce investigation results without implementation or commit proposals.

### 16.5 Plan revisions

Material changes to Work Unit scope or dependencies must be reflected in the plan.

Existing authorization must be reassessed when its assumptions no longer apply.

---

## 17. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Meaningful Work Units

Work Units represent coherent engineering objectives rather than arbitrary implementation steps.

### INV-002 — Adaptive sizing

Work Unit size must be proportional to scope, risk, and reviewability.

### INV-003 — Explicit scope

Each Work Unit must have a defined implementation boundary.

### INV-004 — Traceable dependencies

Dependencies affecting execution order or correctness must be explicit.

### INV-005 — Evidence-backed verification

Verification claims require observed evidence.

### INV-006 — Separate engineering states

Implementation, verification, acceptance, and publication must remain distinguishable.

### INV-007 — One proposed commit per meaningful unit

One proposed commit per implementation Work Unit is the default delivery strategy.

### INV-008 — No mandatory commit for read-only work

Read-only investigations do not require artificial commit proposals.

### INV-009 — Publication disabled by default

Stage, commit, push, PR creation, and merge require explicit authorization.

### INV-010 — No implicit authorization chaining

Permission for one Git operation does not imply permission for subsequent operations.

### INV-011 — Preserve unrelated changes

Work Unit delivery must not include unrelated workspace modifications.

### INV-012 — Verified staging boundary

Authorized commits must use an inspected, intended staged change set.

### INV-013 — Reviewable checkpoints

The workflow must support human review at meaningful Work Unit boundaries.

### INV-014 — Plan revision awareness

Material Work Unit changes require plan and authorization reassessment.

### INV-015 — Honest delivery reporting

Delivery records must distinguish proposals from executed and verified outcomes.

### INV-016 — Recoverable execution

Long-running Work Units must integrate with durable checkpoints and safe resumption.

---

## 18. Alternatives Considered

The following alternatives summarize the tradeoffs relevant to the accepted decision.

### 18.1 One commit per entire task

**Advantages**

- Simple delivery.
- Minimal commit count.

**Disadvantages**

- Large changes become difficult to review.
- Intermediate engineering boundaries are lost.
- Recovery and selective rollback become harder.

**Disposition:** Acceptable for small tasks, but not the universal strategy.

### 18.2 One commit per file

**Advantages**

- Predictable mechanical rule.
- Small diffs.

**Disadvantages**

- Splits coherent changes.
- Produces incomplete intermediate states.
- Separates implementation from related tests.

**Disposition:** Rejected.

### 18.3 One commit per tool invocation

**Advantages**

- Fine-grained history.

**Disadvantages**

- Excessive fragmentation.
- Poor engineering meaning.
- High review overhead.

**Disposition:** Rejected.

### 18.4 Automatic commit and push after tests

**Advantages**

- Fast automation.
- Minimal human intervention.

**Disadvantages**

- Tests may not cover all risks.
- Unrelated changes may be included.
- Publication authority becomes implicit.
- Repository policy may be bypassed.

**Disposition:** Rejected as the default.

### 18.5 Mandatory approval after every step

**Advantages**

- Frequent human control.

**Disadvantages**

- Excessive interruptions.
- Approval fatigue.
- Poor efficiency.

**Disposition:** Rejected as a universal requirement.

### 18.6 Unbounded Work Units

**Advantages**

- Minimal decomposition effort.

**Disadvantages**

- Weak reviewability.
- Difficult recovery.
- Unclear verification boundaries.
- Increased risk of scope drift.

**Disposition:** Rejected.

---

## 19. Consequences

### 19.1 Positive consequences

- More reviewable changes.
- Clearer implementation boundaries.
- Better verification traceability.
- Improved recovery from interrupted work.
- Reduced accidental publication.
- Cleaner Git history.
- Better human control.
- More predictable task progression.
- Support for both small fixes and complex projects.

### 19.2 Costs

- Work Unit planning.
- Dependency tracking.
- Change-boundary management.
- Verification reporting.
- Commit proposal generation.
- Human review checkpoints.
- Git staging safeguards.
- Delivery state tracking.

### 19.3 Risks

**Over-decomposition**

Too many Work Units may create unnecessary overhead.

Mitigation: Use meaningful engineering boundaries.

**Under-decomposition**

Oversized units may be difficult to review or verify.

Mitigation: Split at coherent architectural and verification boundaries.

**Commit contamination**

Unrelated staged changes may be included.

Mitigation: Verify exact staged content.

**False verification**

A Work Unit may be marked verified without sufficient evidence.

Mitigation: Require observed verification results.

**Authorization confusion**

Commit preparation may be mistaken for commit permission.

Mitigation: Separate proposal, execution, and publication states.

**Plan drift**

Work Units may expand during implementation.

Mitigation: Reassess scope and authorization on material changes.

---

## 20. Implementation Guidance

### 20.1 Initial milestones

Work Unit modeling should begin in M4.

Controlled execution integration belongs to M5.

Verification and delivery preparation belong to M6.

### 20.2 Minimum viable Work Unit model

The initial implementation should support:

- Stable Work Unit identity.
- Task and plan revision binding.
- Objective.
- Scope.
- Dependencies.
- Acceptance criteria.
- Verification requirements.
- Lifecycle status.
- Proposed commit metadata.

### 20.3 Minimum viable delivery workflow

The initial delivery implementation should support:

- Actual change inspection.
- Work Unit change attribution.
- Verification evidence collection.
- Proposed commit title and body.
- Delivery summary.
- Explicit publication status.

### 20.4 Suggested logical interfaces

Possible operations include:

```text
decompose_task_into_work_units(plan)

validate_work_unit_dependencies(work_units)

prepare_work_unit_execution(work_unit, context, grant)

collect_work_unit_changes(work_unit, repository)

verify_work_unit(work_unit, evidence)

prepare_commit_proposal(work_unit, changes)

prepare_delivery_record(task, work_units)

validate_delivery_readiness(delivery)
```

These are conceptual operations, not mandated function signatures.

### 20.5 Git operations

Stage, commit, push, PR creation, and merge must remain separate guarded operations.

### 20.6 Avoid premature complexity

The initial implementation does not require:

- Parallel Work Unit execution.
- Automatic merge queues.
- Distributed task orchestration.
- Complex dependency scheduling.
- Automatic release management.
- Autonomous PR merging.

These may be considered later if justified.

---

## 21. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Small localized bug fix | One coherent Work Unit |
| Multi-component feature | Meaningful units with explicit dependencies |
| Read-only investigation | No mandatory commit proposal |
| Implementation completed but tests unavailable | Not marked fully verified |
| Tests executed successfully | Observed results recorded |
| Tests fail | Failure retained in delivery record |
| Work Unit scope expands | Plan and authorization reassessment |
| Unrelated dirty files exist | Preserved and excluded from delivery |
| Existing staged changes exist | Not silently included |
| Commit proposal generated | No Git commit executed |
| Staging not authorized | No staging performed |
| Commit not authorized | No commit performed |
| Push not authorized | No push performed |
| PR creation not authorized | No PR created |
| Merge not authorized | No merge performed |
| Authorized commit with staged mismatch | Commit rejected |
| Review checkpoint reached | Workflow can suspend for review |
| Execution interrupted | Checkpoint retained |
| Resume after workspace change | Revalidation required |
| Delivery report generated | Proposed and executed operations distinguished |
| Partial verification | Limitations reported |
| Historical Work Unit retrieved | Original plan and evidence references preserved |

### 21.1 Test isolation

Tests must use disposable repositories and controlled Git adapters.

### 21.2 Negative testing

Tests must cover unauthorized publication, staging contamination, scope drift, and invalid state transitions.

### 21.3 Evidence

Verification must rely on observed behavior.

A proposed commit message is not evidence that a commit exists.

---

## 22. Related Decisions and Contracts

### Related ADRs

**ADR-003 — Revision-Scoped Graph Snapshots**

Establishes coherent historical knowledge.

**ADR-004 — Workspace Consistency**

Defines preservation of unrelated changes and file-level protection.

**ADR-005 — Git Preflight**

Establishes repository baseline and branch coordination.

**ADR-009 — Immutable Context Packages**

Defines reproducible task context.

**ADR-010 — Controlled Execution**

Defines authorization and guarded operations.

**ADR-012 — Adaptive Planning**

Defines planning profiles, plan revisions, and approval checkpoints.

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

## 23. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact Work Unit identifier format.
2. The serialized lifecycle state vocabulary.
3. The algorithm for recommending Work Unit boundaries.
4. The representation of dependency relationships.
5. The method for attributing partial-file changes to Work Units.
6. The default commit message convention when none exists.
7. The exact human review interface.
8. The delivery artifact storage format.
9. The strategy for handling Work Units that cannot be independently verified.
10. The policy for reworking previously accepted Work Units.
11. The eventual parallel execution model.
12. The mechanism for associating actual Git commits with Work Unit records.

These questions should be resolved during implementation when supported by concrete requirements.

They must preserve the architectural invariants established above.

---

## 24. Acceptance and Compliance

ADR-011 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Tasks are decomposed into meaningful Work Units.
- Work Unit size is adaptive.
- Scope and dependencies are explicit.
- Verification evidence is retained.
- Implementation, verification, acceptance, and publication remain separate.
- One proposed commit per meaningful implementation Work Unit is the default.
- Read-only work does not require artificial commit proposals.
- Unrelated changes are preserved.
- Git staging and publication require explicit authorization.
- Human review checkpoints are supported.
- Delivery records accurately represent observed outcomes.

Compliance requires implementation and test evidence.

The existence of this ADR does not establish that these capabilities have been implemented.

---

## 25. Decision Summary

AEW organizes implementation into adaptive Work Units representing meaningful engineering changes.

Each implementation Work Unit normally produces one proposed Git commit, including a title, body, and verification summary.

Work Units support explicit scope, dependencies, acceptance criteria, verification evidence, and human review checkpoints.

Implementation completion, verification, acceptance, commit execution, and remote publication remain separate states.

Stage, commit, push, PR creation, and merge are disabled by default and require explicit authorization.

**AEW should deliver coherent engineering progress in reviewable units, without confusing prepared work with permission to publish it.**