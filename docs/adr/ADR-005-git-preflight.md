# ADR-005 — Git Preflight and Task Branch Strategy

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Git repository preflight, integration baseline verification, task branch creation, branch naming, remote coordination, and pull request awareness  
**Related milestones:** M1 — Read-Only Repository Preflight; M5 — Authorization and Controlled Execution

---

## 1. Context

The Adaptive Engineering Workbench (AEW) operates on existing software repositories where multiple developers, AI agents, and automated processes may work concurrently.

Before implementing a task, AEW must understand the repository's actual state.

Without repository preflight, an AI coding agent may:

- Begin work from an outdated integration branch.
- Modify an inappropriate branch.
- Create a task branch from an incorrect baseline.
- Duplicate an existing task branch.
- Overlap with an active pull request.
- Ignore concurrent work affecting the same components.
- Misinterpret local remote-tracking references as current remote state.
- Modify files already changed by another developer.
- Produce a change that is difficult to integrate or review.

These risks are not limited to large projects.

Even a small bug fix may depend on code that has recently changed on the integration branch.

AEW therefore requires a mandatory, evidence-backed repository preflight before implementation.

The preflight must remain proportionate to the task while preserving its safety requirements.

---

## 2. Decision

AEW will require **read-only Git and repository coordination preflight before implementation begins**.

For new implementation tasks, AEW will propose a dedicated task branch based on the latest verified integration branch revision.

The branch naming convention will be configurable.

Preflight must inspect local repository state, remote baseline information, relevant branch collisions, and active pull request coordination.

The preflight process must distinguish completed checks from incomplete or unavailable checks.

### 2.1 Core requirements

The preflight must establish:

1. Repository identity.
2. Current branch and HEAD.
3. Local workspace state.
4. Configured integration branch.
5. Latest verified remote integration revision.
6. Availability of the required baseline locally.
7. Proposed task branch name.
8. Local and remote branch collisions.
9. Relevant active pull requests.
10. Potential concurrent work.
11. Known risks and unresolved uncertainties.

### 2.2 Read-only boundary

Preflight must not implicitly:

- Fetch or update local Git references.
- Switch branches.
- Create branches.
- Stage files.
- Commit changes.
- Push branches.
- Create or modify pull requests.
- Merge changes.

Remote inspection may use read-only APIs without changing repository state.

If synchronization is required, AEW must propose a separate, authorized operation.

### 2.3 Implementation boundary

Completing preflight does not itself authorize implementation.

Preflight establishes repository readiness evidence.

Implementation requires the appropriate task plan and authorization.

---

## 3. Repository Identity

AEW must establish which repository it is operating on.

### 3.1 Required observations

Repository identification should include:

- Canonical local repository root.
- Git directory or worktree identity.
- Current branch or detached HEAD state.
- Current HEAD commit.
- Configured remote identity.
- Repository provider identity when available.

### 3.2 Explicit remote identity

Remote coordination must use an explicit repository identity.

For GitHub, this normally takes the form:

`owner/repository`

AEW must not assume that the current directory's remote configuration necessarily identifies the intended GitHub repository.

### 3.3 Multiple remotes

Repositories may have multiple remotes, including:

- `origin`
- `upstream`
- Fork-specific remotes.
- Organization-specific integration remotes.

The integration remote must be identified through configuration or verified repository context.

The name `origin` is a default convention, not a universal architectural requirement.

### 3.4 Worktrees

Git worktrees may share repository objects and references while maintaining separate working directories.

AEW must distinguish the current worktree from the broader repository.

A branch being used by another worktree must not be treated as freely available for checkout.

---

## 4. Integration Branch Strategy

### 4.1 Configured integration branch

AEW must support a configurable integration branch.

The initial configuration default is:

```json
{
  "git": {
    "integration_branch": "master"
  }
}
```

Projects may instead use:

- `main`
- `develop`
- A release integration branch.
- Another explicitly configured branch.

AEW must not silently substitute a different integration branch when the configured one is unavailable.

### 4.2 Latest verified baseline

New task branches should originate from the latest verified integration branch revision.

A verified baseline requires sufficient evidence to establish the intended remote branch's current commit and its relationship to locally available Git objects.

### 4.3 Remote observation

AEW should obtain the integration branch's current remote commit through a read-only provider operation.

For GitHub, this may use an authenticated read-only API request.

### 4.4 Local observation

AEW should inspect:

- Locally known remote-tracking reference.
- Local integration branch reference.
- Availability of the remote commit object.
- Relevant divergence between references.

### 4.5 Baseline reconciliation

AEW must distinguish the following conditions.

| Condition | Meaning |
|---|---|
| Verified and locally available | Remote baseline observed and required commit available locally |
| Remote ahead | Local references or objects do not represent the latest observed remote state |
| Local divergence | Local integration branch differs from the verified remote baseline |
| Remote unavailable | Current remote revision cannot be established |
| Local object unavailable | Remote revision is known but required Git object is absent locally |
| Ambiguous identity | Intended integration repository or branch cannot be established |

Only the first condition establishes a ready baseline for branch creation without additional synchronization.

### 4.6 Synchronization

If the required commit is not locally available, AEW may propose a synchronization operation.

Synchronization must be separately authorized because it can modify local Git state.

The preflight phase must not silently perform synchronization.

### 4.7 Freshness and concurrency

Remote observations are time-bound.

A remote branch may advance after inspection.

AEW must record the observed revision and revalidate relevant assumptions before operations that depend on its continued freshness.

A previously successful preflight is not an indefinite guarantee.

---

## 5. Task Branch Strategy

### 5.1 Dedicated branches

New implementation tasks should normally use dedicated task branches.

This provides:

- Clear task boundaries.
- Easier review.
- Better change isolation.
- Predictable delivery.
- Reduced accidental modification of integration branches.

### 5.2 Branch creation baseline

A new task branch must be created from the verified integration baseline rather than blindly branching from the current checkout.

### 5.3 Branch naming

The default naming convention is:

`{prefix}{type}/{issue}-{slug}`

Default prefix:

`mb/`

Example:

`mb/fix/142-null-customer-response`

### 5.4 Branch types

Initial branch type mappings may include:

| Task category | Branch type |
|---|---|
| Bug fix | `fix` |
| Feature | `feat` |
| General task | `task` |
| Refactoring | `refactor` |
| Documentation | `docs` |

Additional categories may be supported through validated configuration.

### 5.5 Configurability

The following must remain configurable:

- Integration branch.
- Integration remote.
- Branch prefix.
- Branch naming pattern.
- Branch collision policy where appropriate.

Configuration must not override repository security policy.

### 5.6 Git-native validation

Generated branch names must be validated using Git's native reference rules.

A regular expression alone is insufficient.

### 5.7 Branch collisions

Before creating a branch, AEW must inspect relevant local and remote references.

If the proposed branch already exists, AEW must not silently overwrite or reuse it.

The system may propose:

- Reusing an existing task branch after verification and authorization.
- Selecting a distinct branch name.
- Investigating whether the task is already in progress.

### 5.8 Protected branches

AEW must respect repository branch protection and operational policy.

A configured naming convention does not authorize modification of a protected branch.

### 5.9 Branch creation authorization

Creating a branch is a distinct operation.

The Approval Contract includes `create_branch`.

Preflight may propose a branch, but it must not create one without appropriate authorization.

---

## 6. Working-Tree Preflight

ADR-004 establishes AEW's workspace consistency model.

ADR-005 requires that model to be applied during repository preflight.

### 6.1 Required inspection

Preflight must inspect:

- Staged changes.
- Unstaged changes.
- Untracked files.
- Deleted files.
- Renamed files.
- Relevant merge conflicts.

### 6.2 Dirty repositories

A dirty repository does not automatically block every task.

AEW must assess whether existing changes overlap the intended task scope.

### 6.3 Overlap classifications

Preflight must distinguish:

- No existing changes.
- Non-overlapping changes.
- Overlapping changes.
- Unknown relationship.

### 6.4 Overlapping modifications

If existing modifications overlap the intended task, AEW must identify the affected paths and preserve those changes.

The system must not silently discard, overwrite, or stage them.

### 6.5 Unknown scope

If the task scope cannot yet be established, AEW must report that uncertainty.

A task may continue through read-only investigation to refine its scope.

Unknown overlap must not be interpreted as clearance for modification.

### 6.6 Semantic coordination

Path non-overlap is not proof of architectural independence.

The Project Brain may identify relationships between affected components.

Such findings should enrich the preflight report when evidence is available.

---

## 7. Pull Request Coordination

Active pull requests may contain work relevant to the proposed task.

AEW must inspect relevant PR information before implementation.

### 7.1 Required information

Where supported by the repository provider, inspect:

- PR identifier.
- Title.
- State.
- Base branch.
- Head branch.
- Head commit.
- Changed files.
- Relevant issue references.
- Available dependency information.

### 7.2 Relevance assessment

A PR may be relevant when it:

- Changes the same files.
- Changes related components.
- Modifies a shared contract.
- Addresses the same issue.
- Introduces a dependency affecting the task.
- Uses a branch that collides with the proposed task branch.

### 7.3 Conservative overlap

A lack of matching file paths does not prove independence.

When file lists are incomplete or dependency information is unavailable, AEW must preserve uncertainty.

### 7.4 PR enumeration completeness

AEW must not treat a truncated list of active PRs as exhaustive.

Pagination and provider limits must be handled explicitly.

If enumeration cannot be completed, preflight must report incomplete coordination evidence.

### 7.5 Changed-file completeness

A PR's changed-file list must be complete before AEW uses it to conclude that no path overlap was found.

A truncated file list must not produce a false non-overlapping result.

### 7.6 Existing work

If an active PR appears to address the requested task, AEW should report it and propose coordination rather than immediately creating duplicate work.

### 7.7 Provider independence

GitHub is the initial provider.

The architectural requirement is repository coordination awareness, not permanent dependence on GitHub-specific APIs.

---

## 8. Preflight Result Model

Preflight must produce a structured, evidence-backed report.

### 8.1 Required report contents

A complete report should identify:

- Repository.
- Current branch.
- Current HEAD.
- Integration branch.
- Observed remote integration commit.
- Locally available baseline.
- Workspace state.
- Intended task scope.
- Overlap assessment.
- Proposed task branch.
- Branch collision status.
- Relevant PRs.
- Coordination findings.
- Evidence references.
- Missing checks.
- Overall status.

### 8.2 Status model

The initial implementation uses:

| Status | Meaning |
|---|---|
| `passed` | All mandatory checks completed without blocking findings |
| `warning` | Mandatory evidence is complete, but nonblocking risks require attention |
| `blocked` | A known condition prevents safe progression |
| `unavailable` | Required evidence could not be established |

### 8.3 Status semantics

`passed` must not mean merely that no error was detected.

It means required checks were actually completed and produced sufficient evidence.

`warning` must not conceal missing mandatory checks.

`blocked` identifies a known blocking condition.

`unavailable` identifies missing or incomplete evidence.

### 8.4 Multiple conditions

A report may contain both blocking conditions and unavailable checks.

The report must preserve individual findings even when a single overall status is required.

For example, a branch collision may be blocking while PR enumeration is unavailable.

The overall status should not hide either condition.

### 8.5 Local-only preflight

Local Git inspection cannot establish complete remote freshness or PR coordination.

Therefore, a local-only preflight report must not claim full success.

### 8.6 Evidence

Each finding should include enough evidence to explain the conclusion.

Evidence may include:

- Observed Git commit identifiers.
- Git reference names.
- Changed paths.
- Provider response metadata.
- PR identifiers.
- Observation timestamps.
- Completeness indicators.

Credentials and secrets must not be unnecessarily included in reports.

---

## 9. Preflight Workflow

The conceptual workflow is:

```text
Task received
      |
      v
Identify repository
      |
      v
Inspect local Git state
      |
      v
Identify integration branch
      |
      v
Observe remote integration HEAD
      |
      v
Reconcile remote and local baseline
      |
      v
Inspect workspace changes
      |
      v
Generate proposed task branch
      |
      v
Check branch collisions
      |
      v
Inspect relevant active PRs
      |
      v
Assess coordination risks
      |
      v
Produce preflight report
      |
      v
Determine next authorized action
```

The workflow is read-only until a separately authorized operation is requested.

### 9.1 Successful preflight

When all mandatory checks complete and no blocking condition exists, AEW may propose the next step.

This may include requesting authorization to create a task branch.

### 9.2 Incomplete preflight

When evidence is unavailable, AEW must identify the missing checks.

Read-only investigation may continue where safe.

Implementation must not proceed on the assumption that unavailable evidence would have been favorable.

### 9.3 Blocking preflight

When a known blocking condition exists, AEW must report it and propose an appropriate resolution.

It must not silently bypass the condition.

---

## 10. Preflight Freshness

Preflight observations can become stale.

### 10.1 Sources of staleness

Examples include:

- Integration branch advancement.
- New active PRs.
- PR updates.
- Branch creation by another developer.
- Local workspace changes.
- New commits.
- Changes to repository policy.

### 10.2 Revalidation

AEW must revalidate relevant preflight assumptions before operations that depend on them.

For example:

- Branch creation requires current branch collision and baseline checks.
- Implementation requires current workspace consistency.
- Commit preparation requires current change-boundary verification.
- Publication requires current authorization and repository policy checks.

### 10.3 No permanent clearance

A preflight result is an observation, not a permanent permission token.

It must not be reused indefinitely without checking its applicability.

---

## 11. Authorization Integration

Preflight and authorization are separate.

### 11.1 Preflight authority

Preflight establishes repository facts and risks.

It does not grant permission.

### 11.2 Approval Grants

Restricted operations require an appropriate Approval Grant.

Relevant operations include:

- `create_branch`
- `implement`
- `run_tests`
- `stage`
- `commit`
- `push`
- `create_pr`
- `merge`

### 11.3 Plan binding

Authorization must remain bound to the relevant task and plan revision.

A material plan change may require reassessment.

### 11.4 Workspace binding

Authorization must identify the applicable repository, branch, baseline, and workspace context.

### 11.5 Repository policy

Repository policy remains an independent constraint.

An Approval Grant cannot override protected branch rules or other applicable restrictions.

---

## 12. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Mandatory preflight

Implementation requires repository preflight.

### INV-002 — Read-only inspection

Preflight must not implicitly modify local Git state or publish remote changes.

### INV-003 — Verified integration baseline

New task branches must originate from the latest verified integration revision.

### INV-004 — Configurable branch strategy

Integration branch, branch prefix, and naming conventions must be configurable within repository policy.

### INV-005 — Git-native branch validation

Proposed branch names must satisfy Git's reference rules.

### INV-006 — Collision protection

Existing branches must not be silently overwritten or reused.

### INV-007 — Workspace awareness

Preflight must inspect existing local modifications and assess their relationship to task scope.

### INV-008 — Remote freshness honesty

Locally known remote-tracking references must not be assumed current.

### INV-009 — PR coordination

Relevant active pull requests and concurrent work must be considered.

### INV-010 — Incomplete evidence is not success

Missing remote or PR information must not produce a successful complete preflight.

### INV-011 — Explicit findings

Blocking conditions, warnings, and unavailable checks must remain visible.

### INV-012 — Authorization independence

Successful preflight does not authorize restricted operations.

### INV-013 — Revalidation

Preflight assumptions must be revalidated when relevant repository state changes.

### INV-014 — Provider portability

Core preflight semantics must not depend exclusively on GitHub.

---

## 13. Alternatives Considered

The following alternatives summarize the tradeoffs relevant to the accepted architecture.

### 13.1 Branch from the current checkout

**Advantages**

- Simple.
- Requires minimal repository inspection.

**Disadvantages**

- Current checkout may be outdated.
- Current branch may be unrelated to the task.
- Changes may inherit unintended commits.
- Integration history may be inconsistent.

**Disposition:** Rejected as the default new-task strategy.

### 13.2 Always fetch automatically

**Advantages**

- Easier synchronization.
- Reduces stale local references.

**Disadvantages**

- Modifies local Git state.
- May trigger configured Git behavior.
- Requires network access.
- Blurs inspection and mutation boundaries.

**Disposition:** Not selected for read-only preflight. Synchronization remains a separately controlled operation.

### 13.3 Rely only on local Git state

**Advantages**

- Fast.
- Offline.
- Minimal dependencies.

**Disadvantages**

- Remote-tracking references may be stale.
- Active PRs are not visible.
- Remote branch collisions may be missed.
- Concurrent work may be overlooked.

**Disposition:** Insufficient for complete remote-aware preflight.

### 13.4 Require a clean working tree

**Advantages**

- Simplifies some branch and staging operations.

**Disadvantages**

- Disrupts legitimate workflows.
- Encourages unnecessary stashing.
- Does not eliminate concurrency risks.

**Disposition:** Rejected as a universal prerequisite, consistent with ADR-004.

### 13.5 Automatically reuse matching branches

**Advantages**

- Reduces duplicate branch creation.
- May simplify task continuation.

**Disadvantages**

- Branch ownership may be unclear.
- Existing work may be unrelated.
- Baseline and authorization assumptions may differ.

**Disposition:** Not permitted without verification and authorization.

---

## 14. Consequences

### 14.1 Positive consequences

- More reliable task branch baselines.
- Reduced accidental duplicate work.
- Better awareness of concurrent PRs.
- Safer operation in dirty repositories.
- Clearer repository readiness reporting.
- Improved traceability of implementation assumptions.
- Better integration with authorization and Work Units.

### 14.2 Costs

- Additional Git inspection.
- Remote API integration.
- Authentication and availability handling.
- Pagination management.
- Baseline reconciliation logic.
- Preflight freshness tracking.
- More complex failure reporting.

### 14.3 Risks

**Stale remote observations**

A remote branch may advance after inspection.

Mitigation: Record observations and revalidate relevant operations.

**Incomplete PR data**

Provider limits may truncate results.

Mitigation: Require completeness evidence or report unavailable coordination.

**False independence**

Two tasks may affect related behavior without sharing files.

Mitigation: Preserve uncertainty and incorporate Project Brain relationships where supported.

**Excessive preflight overhead**

A large repository may contain many active PRs.

Mitigation: Use efficient discovery and targeted enrichment while preserving completeness requirements.

**Incorrect repository identity**

A local remote may point to an unintended fork or repository.

Mitigation: Verify explicit repository and integration remote identity.

---

## 15. Implementation Guidance

### 15.1 M1 components

The initial implementation should separate:

**Git repository adapter**

Local Git observations and Git-native validation.

**Remote provider adapter**

GitHub issue, PR, and remote branch information.

**Preflight coordinator**

Evidence reconciliation, findings, and overall status.

### 15.2 Existing prototype

The following modules have been drafted:

- `engine/git/repository.py`
- `engine/git/preflight.py`
- `engine/github/client.py`

These modules must be audited and tested before their behavior is considered verified.

### 15.3 Git adapter requirements

Use explicit argument arrays rather than shell-interpolated commands.

Handle:

- Detached HEAD.
- Unborn HEAD.
- Staged changes.
- Unstaged changes.
- Untracked files.
- Renames.
- Unusual filenames.
- Local references.
- Remote-tracking references.

### 15.4 Provider adapter requirements

Use explicit repository identity.

Handle:

- Authentication failure.
- Timeouts.
- Rate limits.
- Invalid responses.
- Pagination.
- Incomplete changed-file lists.
- Missing branches.
- Repository access restrictions.

Provider adapters must not expose unrestricted command execution.

### 15.5 Coordinator requirements

The coordinator must:

- Combine local and remote evidence.
- Preserve uncertainty.
- Distinguish warnings from blockers.
- Identify missing mandatory checks.
- Produce structured results.
- Avoid implicit mutation.
- Support later authorization and branch creation workflows.

### 15.6 Initial scope

M1 should deliver a complete read-only preflight report.

It should not implement branch creation, automatic fetch, or Git publication.

Those capabilities belong to later authorized workflows.

---

## 16. Verification

Compliance should be demonstrated through automated tests and controlled repository scenarios.

| Scenario | Expected result |
|---|---|
| Clean repository with verified baseline | Complete local and remote checks can succeed |
| Local integration ref behind remote | Baseline mismatch detected |
| Remote integration commit absent locally | Baseline unavailable for branch creation |
| Remote provider unavailable | Full preflight cannot pass |
| PR enumeration incomplete | Coordination reported unavailable |
| PR changed-file list truncated | No false non-overlap conclusion |
| Existing local task branch | Collision reported |
| Existing remote task branch | Collision reported |
| Invalid generated branch name | Branch proposal blocked |
| Detached HEAD | State explicitly reported |
| Dirty unrelated workspace | Non-overlap reported with limitations |
| Dirty overlapping workspace | Overlap reported |
| Unknown task scope | Uncertainty preserved |
| Relevant active PR | Coordination risk reported |
| Existing PR addressing same issue | Duplicate-work warning or blocker |
| Preflight without authorization | No branch creation or implementation |
| Remote advances after preflight | Relevant assumptions require revalidation |
| Local-only preflight | Cannot report complete success |
| GitHub unavailable but local Git accessible | Local findings remain available without claiming full clearance |

### 16.1 Integration testing

Use disposable Git repositories and local bare remotes.

Remote-provider behavior should be tested through controlled fixtures or mocked responses.

Live provider tests may be added separately when credentials and suitable test repositories are available.

### 16.2 Read-only verification

Tests must confirm that preflight does not intentionally modify:

- HEAD.
- Branch references.
- Git index.
- Working-tree files.
- Remote repository state.

A stronger security guarantee against hostile repository configuration requires additional process isolation and must not be inferred solely from these tests.

### 16.3 Evidence requirements

Verification reports must include observed results.

Do not claim successful preflight behavior based only on source-code inspection.

---

## 17. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Provides persistence for repository observations and task state.

**ADR-003 — Revision-Scoped Graph Snapshots**

Requires repository revision identity and coherent knowledge observations.

**ADR-004 — Workspace Consistency**

Defines dirty-worktree protection and concurrency requirements.

**ADR-009 — Immutable Context Packages**

Preserves repository revision and coordination evidence in task context.

**ADR-010 — Controlled Execution**

Uses preflight findings and authorization to govern implementation.

**ADR-011 — Adaptive Work Units and Delivery**

Defines task branch delivery and commit boundaries.

**ADR-012 — Adaptive Planning**

Uses preflight risks and uncertainties to inform task planning.

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

## 18. Open Implementation Questions

The accepted architecture does not yet prescribe:

1. The exact remote freshness observation mechanism for each provider.
2. The policy for handling remote advancement during long-running tasks.
3. The initial set of supported Git hosting providers.
4. The strategy for identifying semantic overlap between active PRs.
5. The threshold for classifying a relevant PR as blocking rather than advisory.
6. The exact preflight report serialization format.
7. The policy for reusing an existing task branch.
8. The implementation of separately authorized Git synchronization.
9. The treatment of provider API rate limits during large repository scans.
10. The method for coordinating multiple local worktrees.

These choices should be resolved through implementation evidence and concrete requirements.

They must preserve the invariants defined above.

---

## 19. Acceptance and Compliance

ADR-005 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Preflight precedes implementation.
- Preflight remains read-only.
- Integration baseline freshness is verified.
- New task branches are based on the verified integration revision.
- Branch naming is configurable and Git-valid.
- Existing branch collisions are detected.
- Workspace modifications are assessed.
- Relevant active PRs are considered.
- Incomplete evidence cannot produce full clearance.
- Preflight does not grant implementation or publication authority.

Compliance requires observed test evidence.

The existence of this ADR does not establish that the implementation already satisfies these requirements.

---

## 20. Decision Summary

AEW requires read-only repository preflight before implementation.

The preflight establishes repository identity, current state, integration baseline freshness, task branch naming, branch collisions, workspace overlap, and relevant active PR coordination.

New task branches must originate from the latest verified integration baseline and follow configurable naming conventions.

Incomplete evidence must remain visible and must not be interpreted as success.

Preflight observations are time-bound and require revalidation when relevant repository conditions change.

**AEW must know which repository state it is building upon before it is allowed to change that repository.**