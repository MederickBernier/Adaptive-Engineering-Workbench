# ADR-004 — Workspace Consistency and Concurrent Modification Protection

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Repository workspace integrity, dirty-worktree handling, scoped modifications, concurrent change detection, and guarded filesystem operations  
**Related milestones:** M1 — Read-Only Repository Preflight; M5 — Authorization and Controlled Execution

---

## 1. Context

The Adaptive Engineering Workbench (AEW) is designed to operate within existing software repositories.

These repositories may contain work performed by:

- The engineer.
- Other developers.
- Other AI agents.
- IDE integrations.
- Build tools.
- Code generators.
- Background processes.

The working tree may contain staged, unstaged, untracked, deleted, or renamed files.

A repository may also change while AEW is investigating or implementing a task.

Traditional AI coding workflows sometimes assume that the working tree is entirely available for modification.

This assumption is unsafe.

An AI agent may overwrite unrelated changes, accidentally include another developer's modifications in a commit, or apply a patch against source content that has changed since it was inspected.

Requiring a completely clean working tree before every task would avoid some risks, but it would also introduce unnecessary restrictions.

Engineers routinely maintain unrelated local changes while working on separate tasks.

AEW therefore requires a consistency model that allows safe, scoped work in dirty repositories without sacrificing workspace integrity.

---

## 2. Decision

AEW will implement **scope-aware workspace protection with per-file concurrent modification detection**.

The system must preserve unrelated changes and validate the relevant workspace state before performing controlled modifications.

A dirty working tree does not automatically prevent implementation.

However, AEW must determine whether existing modifications overlap the intended task and whether the proposed operation can be performed safely.

The system must distinguish:

1. Repository-level state.
2. Task-level intended scope.
3. Work Unit modification boundaries.
4. Existing user and external modifications.
5. File versions observed during investigation.
6. File versions present immediately before modification.
7. Authorized operations and protected paths.

### 2.1 Core decision

AEW must not modify a file merely because it appears in an implementation plan.

Before writing, the execution controller must verify that the operation is authorized, that the target is within the permitted scope, and that the file has not changed unexpectedly.

### 2.2 Dirty-worktree policy

Existing changes are classified according to their relationship with the intended task.

| Classification | Meaning | Default handling |
|---|---|---|
| Clean | No observed local changes | Continue applicable checks |
| Non-overlapping | Existing changes appear outside task scope | Preserve and continue cautiously |
| Overlapping | Existing changes intersect intended scope | Require reconciliation before conflicting writes |
| Unknown | Scope or workspace relationship cannot be established | Do not assume independence |

These classifications are observations, not authorization decisions.

A non-overlapping result does not prove that two changes are semantically independent.

### 2.3 Write protection

Controlled writes require:

- Valid authorization.
- Repository identity verification.
- Scope validation.
- Protected-path enforcement.
- File identity verification.
- Expected-content verification.
- Concurrent modification checks.
- Safe handling of unexpected changes.

The execution engine must deny or suspend operations when these requirements cannot be satisfied.

---

## 3. Workspace State Model

AEW must distinguish the committed repository revision from the current working-tree state.

### 3.1 Committed state

The Git HEAD commit identifies the committed repository baseline.

It does not necessarily describe the content currently visible in the working tree.

### 3.2 Index state

The Git index may contain staged changes that differ from both HEAD and the working tree.

AEW must not assume staged content belongs to its current task.

### 3.3 Working-tree state

Working-tree files may contain modifications not present in the Git index.

These modifications may belong to the engineer or another process.

### 3.4 Untracked files

Untracked files are not automatically disposable.

They may contain important work.

AEW must preserve unrelated untracked files and must not overwrite an existing untracked file simply because it is absent from Git history.

### 3.5 Renamed and deleted files

Renames and deletions affect both the original path and the resulting path state.

For scope assessment, AEW must consider the source and destination of a rename.

### 3.6 Workspace observation

A workspace observation should identify:

- Repository identity.
- HEAD commit.
- Current branch or detached state.
- Relevant index state.
- Relevant working-tree state.
- Changed paths.
- Observation time or sequence.
- Workspace fingerprint or equivalent consistency evidence.

The exact fingerprint representation remains an implementation choice.

---

## 4. Scope-Aware Assessment

AEW must evaluate existing modifications relative to the intended task scope.

### 4.1 Intended scope

A task or Work Unit may define its intended scope using:

- Explicit file paths.
- Supported directory expressions.
- Supported path patterns.
- Known component boundaries.

The scope representation must be validated before use.

### 4.2 Overlap detection

A workspace modification overlaps the intended scope when it affects a file or path included in that scope.

For example:

```text
Existing changes:
    frontend/styles.css
    docs/notes.md

Task scope:
    backend/auth/**
```

The changes are path-non-overlapping.

By contrast:

```text
Existing changes:
    backend/auth/TokenService.java

Task scope:
    backend/auth/**
```

The changes overlap.

### 4.3 Unknown scope

When AEW cannot interpret the scope or reliably classify a changed path, the result must be `unknown`.

Unknown must not be converted into non-overlapping.

### 4.4 Semantic overlap

Path independence does not guarantee behavioral independence.

Two files may participate in the same API, database transaction, dependency chain, or shared contract.

The Project Brain may enrich overlap analysis using dependency relationships.

However, graph-assisted analysis remains advisory unless its evidence and coverage justify a stronger conclusion.

### 4.5 Partial knowledge

AEW must not assume that uninvestigated dependencies do not exist.

When dependency coverage is incomplete, the assessment must preserve that limitation.

---

## 5. File-Level Concurrent Modification Detection

Repository state may change between investigation and implementation.

AEW must detect unexpected changes before writing.

### 5.1 Expected-content model

When AEW reads a file for a planned modification, it should retain an expected-content identity.

This may be represented by:

- A cryptographic content digest.
- A versioned file observation.
- An equivalent deterministic comparison mechanism.

The expected identity must be associated with the specific file and execution context.

### 5.2 Pre-write verification

Immediately before modifying a file, AEW must verify that its current content matches the expected content.

If the file has changed unexpectedly, the operation must not proceed automatically.

### 5.3 Example

```text
T0 — AEW reads CustomerService.java
     Expected hash: H1

T1 — Engineer edits CustomerService.java
     Current hash: H2

T2 — AEW attempts modification

     H1 != H2

     Result: Suspend affected write
```

AEW must not silently overwrite the engineer's modification.

### 5.4 Files created during execution

For new files, AEW must verify that the intended destination does not already exist unless replacement is explicitly authorized.

A file appearing after planning but before creation constitutes a concurrency conflict.

### 5.5 File deletion

Deletion requires explicit authorization and confirmation that the target still matches the expected identity.

Deletion must not be treated as an ordinary write without additional safeguards.

### 5.6 Renames

Renaming a file requires validation of:

- Original file identity.
- Source path authorization.
- Destination path authorization.
- Destination existence.
- Relevant concurrency conditions.

### 5.7 Reconciliation

When a conflict occurs, AEW may:

- Suspend the affected Work Unit.
- Report the changed file.
- Refresh relevant context.
- Propose a revised patch.
- Request authorization for an expanded scope.

It must not silently discard the external modification.

---

## 6. Guarded Filesystem Operations

Workspace protection must be enforced by deterministic code.

AI instructions alone are insufficient.

### 6.1 Repository boundary

Every target must resolve within the authorized repository boundary.

Paths escaping the repository must be rejected.

### 6.2 Path traversal

AEW must reject traversal attempts such as:

```text
../outside.txt
../../secrets.env
```

Path validation must not rely solely on simple string-prefix comparisons.

### 6.3 Symlink handling

Symlinks can redirect filesystem operations outside the intended repository or into protected paths.

The guarded filesystem adapter must prevent such escapes.

The implementation may reject symlink traversal entirely for the initial controlled execution milestone.

### 6.4 Protected paths

Protected-path rules take precedence over allowed-path rules.

For example:

```text
Allowed:
    src/**

Protected:
    src/generated/secrets/**
```

A path matching both rules remains protected.

### 6.5 Canonical identity

The engine must validate the effective filesystem target, not merely the user-supplied lexical path.

### 6.6 Time-of-check/time-of-use risks

Checking a path and then opening it later can introduce a race condition.

The guarded filesystem implementation must account for this.

Where supported, operations should use filesystem primitives that reduce path substitution and symlink race risks.

If the platform cannot provide the required guarantee, AEW must limit the operation or report the unsupported safety condition.

### 6.7 Platform differences

AEW must account for relevant filesystem behavior, including:

- Case sensitivity.
- Path normalization.
- Symlinks.
- File permissions.
- Atomic replacement behavior.
- Platform-specific file locking.

The initial implementation should document its supported platforms and guarantees.

---

## 7. Authorization Boundaries

Workspace consistency and authorization are separate concerns.

A file may be safe from a concurrency perspective but still be unauthorized for modification.

Conversely, a file may be authorized but unsafe to modify because its contents changed unexpectedly.

Both conditions must be satisfied.

### 7.1 Approval Grant

The Approval Contract identifies:

- Repository.
- Branch.
- Baseline commit.
- Workspace identity.
- Allowed operations.
- Allowed paths.
- Protected paths.
- Work Unit scope.
- Applicable constraints.

### 7.2 Execution Envelope

The Execution Contract binds an execution to the authorized workspace and permitted operations.

The execution request must not expand the Approval Grant.

### 7.3 Scope changes

If implementation requires modifying files outside the approved scope, AEW must reassess authorization.

A plan may be revised, but the revision must not silently inherit authority that no longer applies.

### 7.4 Repository policy

Repository security policies remain authoritative constraints.

An Approval Grant cannot override protected repository paths or prohibited operations.

---

## 8. Git Index and Commit Protection

AEW must preserve the distinction between workspace modification and Git publication.

### 8.1 Existing staged changes

Pre-existing staged changes must not be assumed to belong to the current Work Unit.

### 8.2 Staging

When staging is authorized, AEW must stage only the intended, verified change boundary.

Broad staging commands that indiscriminately include unrelated changes must not be used.

### 8.3 Commit preparation

Commit proposals must identify the exact Work Unit changes intended for inclusion.

### 8.4 Commit execution

Before an authorized commit, AEW must verify:

- The intended change boundary.
- Current staged content.
- Unrelated staged changes.
- Verification requirements.
- Commit authorization.

### 8.5 Publication

Pushing, creating PRs, and merging remain separately authorized operations.

Workspace consistency does not imply publication permission.

---

## 9. Workspace Fingerprints

AEW requires a mechanism for identifying the workspace state associated with an observation or execution.

### 9.1 Purpose

Workspace fingerprints support:

- Context validity checks.
- Execution resumption.
- Concurrent modification detection.
- Delivery boundary verification.
- Repository state reconciliation.

### 9.2 Required properties

A fingerprint or equivalent observation identity must:

- Be deterministic for its defined scope.
- Identify the repository baseline.
- Account for relevant index and working-tree state.
- Be associated with the observation context.
- Support detection of changes affecting the protected operation.

### 9.3 Scope sensitivity

A whole-repository fingerprint may change because of unrelated modifications.

AEW should distinguish whole-workspace observations from scoped file-level consistency checks.

Unrelated changes should not automatically invalidate safe work when their independence can be established.

### 9.4 Limitations

A fingerprint is evidence of an observed state.

It is not a lock.

It does not prevent changes from occurring after observation.

Therefore, guarded operations still require appropriate pre-write checks.

---

## 10. Execution and Checkpoint Integration

ADR-010 defines controlled execution and durable checkpoints.

ADR-004 supplies the workspace consistency requirements used by that controller.

### 10.1 Execution start

Before beginning a controlled Work Unit, AEW must validate the expected repository and workspace state.

### 10.2 During execution

Before each protected write, AEW must validate relevant file identity and scope.

### 10.3 Suspension

Unexpected changes affecting the current operation must trigger safe suspension or rejection.

### 10.4 Resumption

After interruption, AEW must revalidate:

- Repository identity.
- Branch.
- Baseline commit.
- Workspace observation.
- Relevant file identities.
- Authorization.
- Context applicability.

A checkpoint must not be treated as unconditional permission to continue.

---

## 11. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Preserve unrelated changes

AEW must not overwrite, delete, stage, or commit unrelated workspace changes without explicit authorization.

### INV-002 — Dirty worktrees are supported

A dirty working tree does not automatically prohibit all engineering work.

### INV-003 — Scope-aware classification

Existing changes must be assessed relative to the intended task scope.

### INV-004 — Unknown is not safe

Unsupported or incomplete scope information must not be interpreted as non-overlapping.

### INV-005 — Per-file concurrency protection

Unexpected file modifications must be detected before controlled writes.

### INV-006 — Protected-path precedence

Protected paths override allowed paths.

### INV-007 — Repository confinement

Guarded operations must not escape the authorized repository boundary.

### INV-008 — Symlink and traversal protection

Path resolution must prevent unauthorized filesystem access.

### INV-009 — Authorization independence

Workspace consistency does not replace operation authorization.

### INV-010 — Index isolation

Pre-existing staged changes must not be silently included in AEW commits.

### INV-011 — Safe interruption

Unexpected workspace changes must not cause uncontrolled retries or overwrites.

### INV-012 — Revalidation on resumption

Checkpoint recovery requires renewed workspace consistency checks.

### INV-013 — Evidence-backed observations

Workspace safety claims must be supported by observed repository and filesystem state.

### INV-014 — No implicit ownership

AEW must not assume exclusive ownership of the working tree.

---

## 12. Alternatives Considered

The following alternatives describe the principal architectural tradeoffs relevant to the accepted decision.

### 12.1 Require a clean working tree

**Advantages**

- Simpler initial implementation.
- Fewer local modification scenarios.
- Easier commit preparation.

**Disadvantages**

- Interrupts legitimate engineering workflows.
- Encourages unnecessary stashing.
- Prevents unrelated parallel work.
- Does not eliminate concurrent modification risks.

**Disposition:** Rejected as a universal requirement.

A clean working tree may still be required for specific high-risk operations.

### 12.2 Allow unrestricted writes within the repository

**Advantages**

- Minimal execution restrictions.
- Simple agent integration.

**Disadvantages**

- Unrelated work may be overwritten.
- Authorization boundaries become ambiguous.
- Concurrent modifications are unsafe.
- Delivery may include unintended changes.

**Disposition:** Rejected.

### 12.3 Rely on Git status alone

**Advantages**

- Easy to implement.
- Useful repository-level observations.

**Disadvantages**

- Git status does not prevent races.
- It does not establish file ownership.
- It does not guarantee content identity.
- It does not enforce protected paths.

**Disposition:** Insufficient as the sole protection mechanism.

### 12.4 Rely on AI instructions

**Advantages**

- Low implementation overhead.
- Flexible reasoning.

**Disadvantages**

- Instructions cannot guarantee filesystem confinement.
- Agents may misunderstand scope.
- Concurrent changes require deterministic checks.
- Security-sensitive enforcement becomes unreliable.

**Disposition:** Rejected as an enforcement mechanism.

### 12.5 Isolate every task in a separate worktree

**Advantages**

- Stronger task-level workspace separation.
- Reduced interference with existing local modifications.
- Cleaner commit boundaries.

**Disadvantages**

- Additional lifecycle management.
- Increased storage use.
- More complex integration with existing IDE sessions.
- Does not eliminate all concurrency or authorization risks.

**Disposition:** Useful as a possible execution strategy, but not mandatory for every task.

---

## 13. Consequences

### 13.1 Positive consequences

- Safer AI-assisted implementation.
- Preservation of existing engineering work.
- Support for dirty repositories.
- Better concurrent-agent coordination.
- More reliable checkpoint recovery.
- Cleaner Work Unit delivery.
- Explicit authorization boundaries.
- Reduced accidental overwrites.

### 13.2 Costs

- Additional filesystem validation.
- Per-file content tracking.
- More complex execution state.
- Platform-specific safety considerations.
- Conflict reconciliation workflows.
- More demanding integration testing.

### 13.3 Risks

**False non-overlap**

Path analysis may miss semantic dependencies.

Mitigation: Preserve uncertainty and use Project Brain evidence where available.

**Race conditions**

Filesystem state may change after validation.

Mitigation: Use appropriate guarded filesystem primitives and immediate content checks.

**Excessive suspension**

Overly broad workspace fingerprints may interrupt unrelated work.

Mitigation: Use scoped consistency checks.

**Index contamination**

Unrelated staged changes may be included accidentally.

Mitigation: Verify exact staging and commit boundaries.

**Unsafe path handling**

Symlinks or path normalization may bypass lexical checks.

Mitigation: Enforce canonical filesystem boundaries and platform-aware protections.

---

## 14. Implementation Guidance

### 14.1 M1 — Read-only assessment

The initial preflight implementation should provide:

- Git status inspection.
- Changed-path enumeration.
- Rename source and destination handling.
- Scope expression validation.
- Conservative overlap classification.
- Evidence-backed findings.

M1 must not claim that lexical overlap analysis is equivalent to write authorization.

### 14.2 M5 — Guarded execution

The controlled execution implementation must introduce:

- Authorized filesystem adapters.
- Canonical path validation.
- Protected-path enforcement.
- Per-file expected-content tracking.
- Concurrent modification detection.
- Safe file creation.
- Safe replacement.
- Safe rename and deletion controls.
- Checkpoint revalidation.

### 14.3 Suggested interfaces

Possible logical operations include:

```text
observe_workspace(repository, scope)

classify_overlap(observation, intended_scope)

validate_write_target(grant, execution, path)

verify_expected_content(path, expected_identity)

apply_guarded_change(operation, expected_identity)

revalidate_checkpoint(checkpoint, workspace)
```

These are conceptual interfaces, not mandated Python function signatures.

### 14.4 Error behavior

Guarded operations should return structured errors identifying:

- Failed invariant.
- Affected path.
- Expected state.
- Observed state, where safe to disclose.
- Whether retry or reconciliation is appropriate.

Do not silently retry a conflicting write with updated expectations.

### 14.5 Auditability

The engine should retain evidence of:

- The authorized scope.
- The file observation used.
- The attempted operation.
- The consistency result.
- The final operation outcome.

Sensitive file contents should not be unnecessarily copied into logs.

---

## 15. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Clean repository | Workspace classified clean |
| Dirty repository with unrelated changes | Non-overlapping classification where supported |
| Dirty repository with relevant changes | Overlap reported |
| Unsupported scope expression | Unknown classification |
| Rename into scope | Overlap detected |
| Rename out of scope | Original path overlap detected |
| Untracked file at proposed destination | Creation rejected |
| File changes after observation | Guarded write rejected or suspended |
| Protected path inside allowed directory | Modification denied |
| Symlink escapes repository | Modification denied |
| Path traversal attempts | Modification denied |
| Existing staged changes | Excluded from unrelated Work Unit commit |
| Concurrent file replacement | Unsafe operation rejected |
| Checkpoint resumed after file change | Revalidation detects mismatch |
| Unauthorized file operation | Denied independently of workspace consistency |
| Dirty but unrelated workspace | Safe authorized work can proceed without deleting unrelated changes |

### 15.1 Test isolation

Filesystem tests must use disposable directories and repositories.

No test should intentionally modify the developer's real working tree.

### 15.2 Platform testing

Where platform behavior affects guarantees, tests should cover the supported operating systems.

A guarantee demonstrated on Linux must not automatically be assumed to hold identically on Windows.

### 15.3 Security testing

Negative tests should include:

- Symlink substitution.
- Path traversal.
- Case-normalization differences.
- Unexpected file creation.
- Concurrent file modification.
- Concurrent rename.
- Protected-path overlap.
- Unauthorized scope expansion.

The implementation must document unsupported safety conditions rather than silently bypass them.

---

## 16. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Provides local persistence for workspace observations and execution state.

**ADR-003 — Revision-Scoped Graph Snapshots**

Requires workspace observations to distinguish committed and uncommitted source states.

**ADR-005 — Git Preflight**

Uses workspace assessment before implementation.

**ADR-009 — Immutable Context Packages**

Binds context to repository and workspace observations.

**ADR-010 — Controlled Execution**

Enforces guarded operations and checkpoint revalidation.

**ADR-011 — Adaptive Work Units and Delivery**

Requires isolated change boundaries and protection of unrelated staged content.

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

## 17. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact workspace fingerprint format.
2. The hash algorithm for expected-content verification.
3. The initial supported filesystem platforms.
4. Whether controlled writes use direct filesystem operations, temporary files, or atomic replacement.
5. Whether isolated Git worktrees become the preferred strategy for some tasks.
6. The exact supported path-pattern language.
7. The mechanism for coordinating multiple local AEW processes.
8. The policy for reconciling overlapping user modifications.
9. The precise approach to race-resistant path resolution on each platform.

These choices should be resolved during implementation using concrete requirements and tests.

They must not weaken the invariants established by this ADR.

---

## 18. Acceptance and Compliance

ADR-004 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Dirty repositories are assessed rather than automatically discarded.
- Unrelated changes are preserved.
- Overlapping changes are identified.
- Unknown scope remains unknown.
- Protected paths are enforced.
- Concurrent modifications are detected before writes.
- Filesystem operations remain within authorized boundaries.
- Existing staged content is not silently incorporated into AEW commits.
- Checkpoint recovery revalidates workspace consistency.

Compliance requires observed test evidence.

The existence of this document does not establish that the implementation already satisfies these requirements.

---

## 19. Decision Summary

AEW will support engineering work in dirty repositories through scope-aware workspace assessment and deterministic file-level concurrency protection.

The system must distinguish existing modifications from task-owned changes, preserve unrelated work, and validate expected file content before controlled writes.

Authorization, filesystem safety, and workspace consistency are independent requirements that must all be satisfied.

**AEW may operate within a shared working tree, but it must never assume that the working tree belongs exclusively to the agent.**