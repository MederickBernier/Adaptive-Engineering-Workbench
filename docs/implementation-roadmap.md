# Adaptive Engineering Workbench (AEW)
# Implementation Roadmap

**Document:** `docs/implementation-roadmap.md`  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Status:** Proposed implementation roadmap  
**Last updated:** 2026-11-22

---

## 1. Purpose

This document defines the incremental implementation strategy for the Adaptive Engineering Workbench (AEW).

AEW is a local-first, skill-first hybrid engineering orchestration system designed to combine AI-assisted reasoning with deterministic enforcement, persistent project knowledge, and controlled software delivery.

The roadmap translates the approved architecture into executable development milestones.

It is intended for human engineers and AI coding agents, including Codex.

The roadmap must remain subordinate to the accepted Architecture Decision Records (ADRs) and the project's documented invariants.

### 1.1 Guiding principle

**Build the smallest complete, verifiable engineering capability before expanding the system.**

Implementation should prioritize functional vertical slices rather than constructing every subsystem independently before any end-to-end workflow is available.

### 1.2 Roadmap objectives

The roadmap aims to:

- Establish a reproducible development environment.
- Validate existing contracts and drafted implementations.
- Deliver a useful read-only engineering workflow early.
- Introduce persistent project intelligence incrementally.
- Separate planning, authorization, execution, and publication.
- Preserve architectural correctness without excessive ceremony.
- Support measurable progress through milestone exit criteria.

### 1.3 Implementation status terminology

All implementation tracking must use the following states:

| Status | Meaning |
|---|---|
| Planned | Approved for future implementation |
| Drafted | Source or design exists but has not been verified |
| In progress | Implementation or verification is underway |
| Blocked | A known dependency prevents completion |
| Verified | Acceptance criteria have been demonstrated with evidence |
| Deferred | Intentionally postponed |

A drafted module must not be described as implemented and verified merely because source code exists.

---

## 2. Implementation Strategy

### 2.1 Skill-first hybrid approach

AEW consists of two primary implementation layers.

**Skill layer**

Provides adaptive engineering reasoning, task interpretation, investigation guidance, planning, and delivery preparation.

**Engine layer**

Provides deterministic validation, persistent state, repository inspection, authorization enforcement, guarded execution, and evidence recording.

The engine should remain relatively small.

Engineering reasoning should not be reimplemented as a large collection of rigid engine rules when an AI skill can perform it appropriately.

Conversely, authorization and safety guarantees must not rely solely on AI instructions.

### 2.2 Vertical-slice development

Each milestone should deliver a coherent capability with:

1. A defined input.
2. A bounded responsibility.
3. An explicit output.
4. Observable failure behavior.
5. Automated verification.
6. Documentation reflecting actual behavior.

Avoid creating broad abstractions for capabilities that have not yet been exercised.

### 2.3 Progressive complexity

AEW itself supports Quick, Standard, Deep, and Explore planning profiles.

Its implementation should follow the same philosophy.

Small, localized improvements should not require extensive design ceremonies.

Changes affecting architectural invariants, contract compatibility, authorization, persistence, or execution boundaries require deeper review.

### 2.4 Human authority

Throughout development:

- Repository modifications require appropriate authorization.
- Unrelated workspace changes must be preserved.
- Commit execution is disabled by default.
- Push, PR creation, and merge are disabled by default.
- Architectural changes require explicit review.
- Verification results must be evidence-backed.

Codex may propose changes and prepare delivery artifacts, but must not interpret this roadmap as permission to publish changes.

---

## 3. Architecture Dependencies

The following decisions govern the implementation roadmap.

| ADR | Architectural concern | Primary milestone |
|---|---|---|
| ADR-003 | Revision-scoped graph snapshots | M2 |
| ADR-004 | Workspace consistency | M1, M5 |
| ADR-005 | Git preflight | M1 |
| ADR-006 | Project intelligence profile | M2 |
| ADR-007 | Staged discovery and invalidation | M2 |
| ADR-008 | Progressive knowledge depth | M2 |
| ADR-009 | Context Packages | M3 |
| ADR-010 | Controlled execution | M5 |
| ADR-011 | Work Units and delivery | M4, M6 |
| ADR-012 | Adaptive planning | M4 |

ADR-001 and ADR-002 are reserved for earlier architectural decisions that must be confirmed before their documentation is finalized.

This roadmap must not invent or retroactively approve their contents.

---

## 4. Milestone Overview

| Milestone | Deliverable | Dependency |
|---|---|---|
| M0 | Reproducible repository and verified baseline | None |
| M1 | Read-only Git/GitHub preflight | M0 |
| M2 | Persistent Project Brain foundation | M0, M1 interfaces |
| M3 | Immutable Context Packages | M2 |
| M4 | Adaptive task planning and Work Units | M1, M3 |
| M5 | Authorization and controlled execution | M4 |
| M6 | Verification and delivery preparation | M5 |
| M7 | Integrated skill-driven workflow | M1–M6 |
| M8 | Hardening and pilot adoption | M7 |

Milestones define dependency order, not necessarily separate releases.

Independent work may proceed concurrently where it does not compromise contracts or create unnecessary integration risk.

---

# 5. M0 — Repository Bootstrap and Verification Baseline

**Priority:** Critical  
**Status:** Verified
**Objective:** Establish a reproducible, testable implementation foundation.

### 5.1 Scope

M0 converts existing drafted source and documentation into a working repository with verified tests and development tooling.

The implementation language remains an open architectural choice.

Python is currently used for the prototype engine and contract tests, but this is not a permanent commitment.

### 5.2 Deliverables

- Verified repository structure.
- Development environment configuration.
- Package and dependency metadata.
- Automated test runner.
- Contract schema validation.
- Cross-contract semantic validation.
- Configuration module tests.
- Git adapter integration tests.
- Local preflight unit tests.
- Initial GitHub adapter unit tests.
- Continuous integration workflow.
- Developer setup documentation.

### 5.3 Existing drafted assets

The following files have been drafted during architectural development:

**Documentation**

- `README.md`
- `docs/architecture.md`
- `aew/skills/aew-task/SKILL.md`

**Contracts**

- `contracts/task.schema.json`
- `contracts/context.schema.json`
- `contracts/approval.schema.json`
- `contracts/execution.schema.json`
- `contracts/delivery.schema.json`

**Engine**

- `engine/config.py`
- `engine/git/repository.py`
- `engine/git/preflight.py`
- `engine/github/client.py`

**Tests**

- `tests/contracts/test_schemas.py`
- `tests/contracts/test_semantics.py`
- `tests/unit/test_unit.py`
- `tests/unit/test_preflight.py`
- `tests/integration/test_git_repository.py`

Contract examples have also been drafted under `contracts/examples/`.

These assets must be inspected in the actual repository before being considered available.

### 5.4 Implementation tasks

#### M0.1 — Repository audit

- Inspect existing files and directory structure.
- Identify missing or incomplete drafted assets.
- Identify incompatible imports and dependencies.
- Identify duplicated or conflicting definitions.
- Verify source files match their documented responsibilities.

#### M0.2 — Development environment

- Establish supported Python versions for the prototype.
- Add project metadata.
- Define development dependencies.
- Configure pytest.
- Configure static analysis and formatting.
- Document installation and test commands.

Do not introduce a complex build system unless required.

#### M0.3 — Contract verification

- Validate all JSON Schemas against Draft 2020-12.
- Validate positive fixtures.
- Verify negative fixtures fail for their intended reasons.
- Test cross-contract invariants.
- Identify incompatible schema assumptions.

The existing Execution Contract requirement that `delivery.prepare_commit` always be true must be reviewed for read-only investigations.

#### M0.4 — Engine baseline

- Run configuration tests.
- Run Git adapter integration tests.
- Run preflight tests.
- Add mocked GitHub client tests.
- Correct confirmed defects.
- Establish deterministic error handling.

#### M0.5 — Continuous integration

CI should initially run:

- Contract tests.
- Unit tests.
- Disposable Git integration tests.
- Static analysis.
- Formatting checks.

External GitHub access must not be required for ordinary CI.

### 5.5 Exit criteria

The [M0 verification record](codex-handoff.md#137-m0-verification-record) captures the observed results and remaining issues.

M0 is verified when:

- The repository can be initialized reproducibly.
- All required dependencies are documented.
- The test suite executes successfully.
- Known baseline defects are resolved or explicitly tracked.
- Drafted and verified capabilities are clearly distinguished.
- CI produces a reliable pass/fail result.

### 5.6 Non-goals

M0 does not implement:

- Project Brain persistence.
- AI-driven code execution.
- Authorization grants.
- Git publication.
- Autonomous task completion.

---

# 6. M1 — Read-Only Repository Preflight

**Priority:** Critical  
**Status:** Partially verified

**Depends on:** M0  
**Primary ADRs:** ADR-004, ADR-005

### 6.1 Objective

Deliver a reliable, evidence-backed repository preflight that detects unsafe or incomplete conditions before implementation begins.

This is AEW's first operational vertical slice.

### 6.2 Components

**Git repository adapter**

Responsible for local repository inspection.

**GitHub adapter**

Responsible for remote repository coordination evidence.

**Preflight coordinator**

Responsible for combining observations and producing a structured result.

### 6.3 Required capabilities

#### Local repository inspection

- Discover repository root.
- Identify current branch and HEAD.
- Detect detached or unborn HEAD.
- Inspect staged, unstaged, and untracked changes.
- Handle renamed and copied paths.
- Identify known local and remote-tracking branches.
- Validate proposed branch names.
- Detect known branch collisions.

#### Integration baseline verification

- Identify the configured integration branch.
- Observe its remote HEAD.
- Observe locally available references.
- Detect mismatches.
- Determine whether the required baseline commit is locally available.
- Report unavailable or stale evidence.

#### GitHub coordination

- Retrieve task-related issues.
- Enumerate relevant open PRs.
- Retrieve PR metadata.
- Retrieve complete changed-file information.
- Identify potential path overlap.
- Identify possible branch dependencies.

#### Workspace assessment

- Compare existing changes with intended task scope.
- Distinguish overlapping, non-overlapping, and unknown cases.
- Include rename source and destination.
- Reject unsupported scope expressions.
- Preserve uncertainty when semantic overlap cannot be ruled out.

### 6.4 Required hardening

The initial drafted adapters require additional work.

**Git adapter**

- Process porcelain output safely.
- Test unusual filenames.
- Validate rename/copy parsing.
- Prevent ambiguous command results.

**GitHub adapter**

- Restrict allowed CLI commands.
- Restrict API endpoints and HTTP methods.
- Handle authentication failure.
- Handle rate limits and timeouts.
- Verify pagination completeness.
- Verify PR file-list completeness.

**Preflight coordinator**

- Distinguish local checks from complete preflight.
- Record evidence.
- Report unavailable dependencies.
- Avoid false success when information is incomplete.

### 6.5 Output

M1 produces a structured preflight report containing:

- Repository identity.
- Current revision.
- Workspace state.
- Integration baseline observations.
- Proposed branch.
- Collision findings.
- Relevant PRs.
- Coordination risks.
- Evidence.
- Unresolved checks.
- Final assessment status.

### 6.6 Exit criteria

M1 is verified when:

- A real repository can be inspected without intentional modifications.
- Local and remote baseline observations can be reconciled.
- Branch collisions are detected.
- Workspace overlap is classified conservatively.
- Incomplete remote information prevents full clearance.
- Findings are supported by evidence.
- Tests cover success and failure scenarios.

### 6.7 Non-goals

M1 does not:

- Create task branches.
- Fetch or update Git references automatically.
- Modify source files.
- Stage changes.
- Execute commits.
- Publish pull requests.

If remote synchronization is required, it must be handled by a separately authorized workflow in a later milestone.

### 6.8 Verification record

Work Units delivered for the M1 baseline:

| Commit | Verified behavior |
|---|---|
| `c9f22c6` | Preserve raw Git status paths and reject incomplete status records. |
| `b21b9c9` | Reconcile the observed integration HEAD with local refs and object availability. |
| `144444d` | Coordinate active PRs with verified file counts and report path overlap, linked issues, and possible branch dependencies. Verified using mocked CLI responses. |
| `9931557` | Detect proposed-branch collisions using live remote refs. |
| `d00641f` | Distinguish known blockers, missing evidence, advisory warnings, and successful preflight. |

On 2026-11-23, a read-only smoke check on the real repository reconciled local and remote `master` at `d00641f`. The proposed branch lookup confirmed an absent test name and detected the occupied `master` ref. Before-and-after comparisons found identical HEAD, refs, and workspace status. The check without a GitHub client returned `UNAVAILABLE`, and the occupied branch produced `BLOCKED`.

`python -m pytest -q` reported 150 passed and 3 skipped on the assessment commit. Ruff lint and format checks passed. The [hosted Actions run](https://github.com/MederickBernier/Adaptive-Engineering-Workbench/actions/runs/45158314459) completed successfully on Linux and Windows.

The remaining M1 verification is an authenticated end-to-end run of the GitHub CLI adapter against a repository with a known open PR and changed files. A read-only REST check found no open PRs in the project repository during closeout. The workstation had no GitHub CLI on PATH or GitHub token in its environment. M2 awaits a new assignment.

---

# 7. M2 — Project Brain Foundation

**Priority:** High  
**Status:** Verified

**Depends on:** M0 and stable M1 repository identity interfaces  
**Primary ADRs:** ADR-003, ADR-006, ADR-007, ADR-008

### 7.1 Objective

Implement persistent, revision-aware project intelligence that reduces repeated repository investigation.

### 7.2 Storage model

The recommended initial storage is:

- One local SQLite database per project.
- Git-backed Markdown knowledge documents.
- Stable identifiers for knowledge entities.
- Logical separation between durable and derived knowledge.

The implementation must preserve the ability to distinguish historical observations from current assertions.

### 7.3 Core entities

The Project Brain should initially represent:

- Project.
- Repository revision.
- Snapshot.
- Component.
- Knowledge assertion.
- Relationship.
- Evidence reference.
- Discovery region.
- Knowledge freshness.
- Investigation depth.

Additional entity types should be introduced only when needed.

### 7.4 Snapshot requirements

- Snapshots are revision-scoped.
- Assertions are immutable.
- Snapshot membership is explicit.
- Historical observations remain reproducible.
- Incompatible revisions are not silently combined.
- Derived knowledge is not automatically treated as durable authority.

### 7.5 Project intelligence profile

AEW must discover:

- Programming languages.
- Frameworks.
- Build systems.
- Package managers.
- Testing tools.
- Linting and formatting conventions.
- CI configuration.
- Relevant repository structure.

Discovery must be evidence-based.

### 7.6 Staged discovery

Repository analysis should proceed incrementally.

**Initial discovery**

Identify broad repository structure and technologies.

**Targeted discovery**

Investigate components relevant to a specific task.

**Deep investigation**

Analyze complex behavior, invariants, dependencies, or risks when required.

### 7.7 Progressive depth

Knowledge depth levels:

| Level | Meaning |
|---|---|
| D0 | Discovery |
| D1 | Structural understanding |
| D2 | Behavioral understanding |
| D3 | Deep semantic and invariant analysis |

Depth and freshness must remain independent.

### 7.8 Targeted invalidation

When repository changes occur:

- Identify affected knowledge regions.
- Mark affected derived assertions as potentially stale.
- Preserve unaffected knowledge where evidence supports it.
- Avoid rebuilding the entire brain unnecessarily.

### 7.9 Exit criteria

M2 is verified when:

- Project knowledge persists across sessions.
- Revision-scoped snapshots are reproducible.
- Evidence is associated with assertions.
- Freshness and depth are independently represented.
- Targeted invalidation is demonstrated.
- Knowledge retrieval works without full-repository reanalysis.

### 7.10 Non-goals

M2 does not require:

- Full semantic understanding of every file.
- A separate graph database server.
- Automated architecture reconstruction for every language.
- A complete semantic code index.
- Distributed synchronization.

### 7.11 Verification record

The MVP uses one SQLite database per checkout with distinct durable and derived assertion kinds. The engineer confirmed this physical layout for the MVP. The broader acceptance histories of ADR-001 and ADR-002 remain open.

| Work Unit | Commit | Observed result |
|---|---|---|
| Snapshot storage | `2ac8c74` | Reopened historical snapshots with explicit membership and provenance, rejected mixed revisions and repository identities, and rolled back a failed publication. |
| Project discovery | `2784b43` | Identified language, framework, package manager, test, CI, and formatting signals from committed files. Targeted discovery excluded an unrelated region, and uncommitted edits did not change the profile. |
| Retrieval and invalidation | `f92d290` | Reopened a snapshot by commit, detected both paths of a rename, marked dependent claims stale, retained unrelated knowledge and its depth, and recovered the original snapshot unchanged. |

The Windows Python 3.13 suite reported **155 passed, 3 skipped**. Ruff lint and formatting passed. A real-repository smoke check published 19 observations at `f92d290`, reopened their SQLite database, retrieved five observations scoped to `engine`, and observed unchanged Git and workspace state. The [hosted M2 CI run](https://github.com/MederickBernier/Adaptive-Engineering-Workbench/actions/runs/45160912271) completed successfully.

Discovery covers committed Git content and recognized file types and manifests. Behavioral and semantic assertions require supplied investigation evidence. Retrieval uses retained snapshots, committed path changes, and explicit dependencies. The Project Brain does not ingest the shared Markdown vault during M2. M1's authenticated live GitHub CLI verification remains open.

---

# 8. M3 — Immutable Context Packages

**Priority:** High  
**Status:** Verified

**Depends on:** M2  
**Primary ADR:** ADR-009

### 8.1 Objective

Create bounded, immutable, evidence-backed Context Packages for engineering tasks.

### 8.2 Required contents

Each package must include:

- Stable package identity.
- Repository identity.
- Repository revision.
- Project Brain snapshot.
- Workspace fingerprint.
- Knowledge coverage.
- Knowledge freshness.
- Investigation depth.
- Relevant components.
- Relevant contracts.
- Evidence references.
- Project conventions.
- Verification guidance.
- Coordination information.
- Known limitations.
- Unresolved uncertainties.

### 8.3 Integrity requirements

- Package identity is stable.
- Package content is immutable.
- Integrity can be verified.
- Evidence provenance is preserved.
- Package expansion does not mutate the original.
- Incompatible revision contexts are not silently mixed.

The Python package codec represents the integrity algorithm and digest as
`package_id = "ctx-sha256-" + SHA-256(canonical content)`. Canonical content is
UTF-8 JSON with sorted object keys, ASCII escaping, compact separators, and
preserved array order. The digest covers the entire document except its own
top-level `package_id`. Duplicate JSON keys and nonfinite numbers are rejected.
Consumers can verify emitted packages with `ContextPackage.from_json()` without
accessing the Project Brain. This checks content integrity. Structural schema
validation, evidence selection, and trusted issuance have separate responsibilities.

### 8.4 Context selection

Selection should prioritize:

- Task relevance.
- Dependency relationships.
- Evidence quality.
- Freshness.
- Required investigation depth.
- Context size constraints.

AEW should not inject the entire Project Brain into every task.

`assemble_context()` selects a literal repository region and available direct
dependencies from a named snapshot. It prioritizes current, direct and verified
claims and bounds the complete serialized package in bytes. A different commit
requires explicit reconciliation. The package records the source revision of
each included assertion and marks affected claims stale. Dirty preflight
evidence requires a caller-supplied workspace fingerprint. Knowledge selection
reads committed evidence.

### 8.5 Exit criteria

`expand_context()` seals a child package from a verified parent and a second
package with the same task, repository, branch, commit, workspace fingerprint,
and snapshot. It preserves the parent evidence, records `parent_package_id`,
and rejects a conflict or a budget too small to include the combined evidence.
For another revision or snapshot, assemble a separate package with explicit
reconciliation as needed.

M3 is verified when:

- A task can receive a valid Context Package.
- Package integrity is verifiable.
- Included assertions are traceable.
- Stale and provisional knowledge is identified.
- Expanded packages preserve original identities and evidence.
- Revision mismatches are rejected or explicitly reconciled.

### 8.6 Verification record

| Work Unit | Commit | Observed result |
|---|---|---|
| Package identity and integrity | `6c7ee93` | Verified deterministic SHA-256 identities, immutable serialization, and rejection of duplicate keys or tampered content. |
| Scoped assembly | `93ac932` | Validated generated packages against the v0.1 schema and verified scope, byte limits, original provenance, and explicit reconciliation. |
| Package expansion | `2859655` | Verified that the child retains the parent's assertions and evidence, links to its digest, and rejects incompatible bindings or conflicting evidence. |

`python -m pytest -q` reported **175 passed, 3 skipped**. Ruff lint and formatting passed. On 2026-11-23, a smoke check against the real repository assembled a parent with six assertions and expanded it to ten. Both artifacts passed Draft 2020-12 validation and reloaded with their original identities. The check rejected a modified evidence reference and observed unchanged Git and workspace state.

The [hosted CI run](https://github.com/MederickBernier/Adaptive-Engineering-Workbench/actions/runs/45162250614) completed successfully for the Linux and Windows matrix on `2859655`.

The codec verifies integrity independently of structural schema validation and trusted issuance. Expansion is restricted to one snapshot and workspace binding. A changed snapshot or revision requires separate assembly and applicable reconciliation. The prior M1 authenticated GitHub CLI verification remains open. M4 awaits a new assignment.

---

# 9. M4 — Adaptive Task Planning

**Priority:** High  
**Status:** Verified

**Depends on:** M1, M3  
**Primary ADRs:** ADR-011, ADR-012

### 9.1 Objective

Transform engineering requests into proportionate, reviewable, revisioned implementation plans.

### 9.2 Planning profiles

**Quick**

For localized, low-risk work with clear acceptance conditions.

**Standard**

For ordinary maintenance and feature work requiring bounded investigation and verification.

**Deep**

For high-risk, cross-cutting, architectural, or complex work.

**Explore**

For tasks where investigation must precede implementation decisions.

### 9.3 Planning inputs

Planning should consider:

- Task objective.
- Repository state.
- Relevant Context Package.
- Known dependencies.
- Scope.
- Risk.
- Uncertainty.
- Verification requirements.
- Coordination findings.

### 9.4 Work Units

Each Work Unit must define:

- Stable identifier.
- Objective.
- Scope.
- Dependencies.
- Acceptance criteria.
- Verification requirements.
- Proposed delivery boundary.

Work Units should represent meaningful engineering changes rather than arbitrary code-size limits.

### 9.5 Plan revisioning

- Plans are revisioned.
- Material plan changes are detectable.
- Authorization binds to plan revisions.
- Changes affecting approved scope require reassessment.
- Historical plans remain traceable.

### 9.6 Exit criteria

M4 is verified when:

- All four planning profiles are supported.
- Small tasks produce lightweight plans.
- Complex tasks can be decomposed into coherent Work Units.
- Work Unit dependencies are validated.
- Plan revisions are tracked.
- Approval requirements are identified.
- Planning alone does not authorize implementation.

### 9.7 Verification record

| Work Unit | Commit | Observed result |
|---|---|---|
| Adaptive assessment | `33dc18e` | Exercised all four profiles, risk-driven escalation, and recorded profile overrides. |
| Advisory plans and Work Units | `dc15388` | Verified schema-compatible Task exports, a single-unit Quick plan, read-only Explore, dependency ordering, and rejection of invalid scope and dependency graphs. |
| Revision history and approvals | `a68371c` | Reopened historical revisions, retained Project Brain snapshots through migration, rejected concurrent stale writes, and flagged material changes for approval reassessment. |

The local suite reported **194 passed, 3 skipped**. Ruff lint and formatting passed. A real-repository smoke check produced two Standard plan revisions from a verified Context Package and local preflight. It validated both Task documents, confirmed dependency order and material-change reassessment, and observed an unchanged Git workspace. Hosted CI for M4 awaits publication.

The engine consumes explicit assessment inputs and Work Unit proposals. It recommends planning depth and checks consistency. Trusted grant issuance, runtime scope enforcement, and publication remain outside M4. The authenticated live GitHub CLI verification from M1 remains open. M5 awaits a new assignment.

---

# 10. M5 — Authorization and Controlled Execution

**Priority:** Critical for write capabilities  
**Status:** Verified for isolated execution

**Depends on:** M4  
**Primary ADRs:** ADR-004, ADR-010, ADR-012

### 10.1 Objective

Introduce controlled repository modification with explicit authorization and deterministic enforcement.

This milestone marks the transition from read-only assistance to authorized implementation.

### 10.2 Authorization engine

The engine must validate:

- Grant identity.
- Trusted approval source.
- Grant lifecycle.
- Task binding.
- Plan revision.
- Repository binding.
- Branch binding.
- Baseline revision.
- Workspace identity.
- Allowed operations.
- Allowed paths.
- Protected paths.
- Work Unit scope.
- Repository policy constraints.

A syntactically valid grant is not automatically authoritative.

### 10.3 Operation controls

Supported operations include:

- Investigation.
- Implementation.
- Test execution.
- Branch creation.
- Staging.
- Committing.
- Pushing.
- PR creation.
- Merging.

Each operation requires independent authorization appropriate to its risk.

### 10.4 Guarded filesystem access

The engine must enforce:

- Repository boundaries.
- Canonical path checks.
- Symlink safety.
- Protected-path precedence.
- Authorized file scope.
- Expected-content checks.
- Concurrent modification detection.
- Preservation of unrelated changes.

### 10.5 Execution Envelopes

Each execution is bound to:

- Task.
- Work Unit.
- Plan revision.
- Context Package.
- Approval Grant.
- Workspace.
- Scope.
- Budget.
- Verification requirements.
- Delivery permissions.

### 10.6 Execution budgets

Support:

- Iteration limits.
- Duration limits.
- Tool-call limits.
- Progress-aware checks.
- Explicit suspension behavior.

Budget exhaustion must not result in unlimited retries.

### 10.7 Durable checkpoints

Checkpoints must preserve enough information to resume safely after interruption.

Resumption requires revalidation of:

- Authorization.
- Repository revision.
- Workspace fingerprint.
- Relevant file versions.
- Context freshness.
- Execution budget.

### 10.8 Exit criteria

M5 is verified when:

- Unauthorized operations are denied.
- Revoked or expired grants cannot execute.
- Scope expansion is rejected.
- Protected paths cannot be modified.
- Concurrent modifications are detected.
- Unrelated workspace changes remain intact.
- Execution can suspend and resume safely.
- Tests demonstrate enforcement independently of AI instructions.

### 10.9 Non-goals

M5 does not require:

- Unrestricted autonomous shell access.
- Automatic publication.
- Distributed execution.
- Multi-host scheduling.
- Self-modifying authorization policies.

### 10.10 Verification record

| Work Unit | Commit | Observed result |
|---|---|---|
| Grant authentication | `584836f` | Verified signed issuer and scope, validity windows, and live revocation. Rejected modified grants and unavailable revocation evidence. |
| Envelope policy | `e536d6a` | Checked task, plan, Work Unit, Context Package, workspace, baseline, and allowed paths. Denied protected paths and unsupported operations. |
| Guarded reads and checkpoints | `f610e2e` | Read exact committed blob versions, preserved unrelated edits, retained budget counters across interruption, and revalidated explicit resumption. |
| Scoped edit review | `9682b9b` | Verified expected file versions and scoped approval, rejected a mismatched object ID, and retained the original checkout content. |
| Disposable execution | `0dfcc38` | Materialized approved text-file creation and replacement inside a disposable Linux container. Verified a host-allowlisted check, rejection of an unrecorded check, omitted protected content, loopback-only networking, a read-only container root, a non-root user, and removal after timeout. |

The local suite reported **207 passed, 3 skipped** with the two Docker integration tests enabled against the locally pinned official Python 3.13 image. Ruff lint and formatting passed. Hosted CI awaits publication.

The delivered adapters use bounded UTF-8 files from a clean, attached checkout's committed Git tree. A trusted host holds the signing and verification key and controls the plan store, revocation source, checkpoint database, Docker engine, image, and check allowlist. Keep those capabilities outside the agent's tool interface. A read or isolated check consumes one iteration and one tool call. A check returns its observed exit code and the original review diff. Test-generated filesystem changes are discarded with the container.

The isolated implementation excludes shared-checkout application, direct Git mutation, and publication. Applying a reviewed diff requires separate engineer authorization through a trusted process. Authenticated M1 GitHub CLI verification and the reviewed v0.1 Execution Contract correction for read-only delivery remain open. M6 awaits a new assignment.

---

# 11. M6 — Verification and Delivery Preparation

**Priority:** High  
**Status:** Verified for delivery preparation

**Depends on:** M5  
**Primary ADR:** ADR-011

### 11.1 Objective

Produce reviewable, evidence-backed delivery artifacts with one proposed commit per meaningful Work Unit.

### 11.2 Verification evidence

Verification records must distinguish:

- Passed.
- Failed.
- Skipped.
- Unavailable.
- Not executed.

A passing result requires evidence from an actual verification procedure.

### 11.3 Commit proposals

Each Work Unit should produce:

- Proposed commit title.
- Proposed commit body.
- Associated file changes.
- Change boundary.
- Verification summary.
- Outstanding risks.

The default commit strategy is one proposed commit per meaningful Work Unit.

### 11.4 Human checkpoints

Before executing a commit:

- Present the proposed boundary.
- Identify staged and unstaged changes.
- Confirm unrelated changes are excluded.
- Confirm required verification evidence.
- Require authorization appropriate to the operation.

### 11.5 Pull request preparation

Generate:

- PR title.
- PR body.
- Included Work Units.
- Verification summary.
- Relevant issue references.
- Known limitations.
- Review considerations.

Preparing a PR is not equivalent to publishing it.

### 11.6 Publication

The following remain disabled by default:

- Stage.
- Commit.
- Push.
- Create PR.
- Merge.

Each must be explicitly authorized before execution.

### 11.7 Exit criteria

M6 is verified when:

- Work Unit changes are traceable.
- Commit proposals are coherent.
- Unrelated changes are excluded.
- Verification evidence is attached.
- PR descriptions are generated.
- Publication is denied without appropriate authorization.
- Sequential human checkpoints are enforced.

### 11.8 Verification record

| Work Unit | Commit | Observed result |
|---|---|---|
| Verification evidence | `034430d` | Persisted observed exit codes with their execution and exact review boundary. Distinguished passed, failed, skipped, unavailable, and not executed without changing the v0.1 Delivery schema. |
| Commit proposals | `32246ff` | Prepared one scoped proposal with file hashes and evidence. A disposable Git test confirmed staged and untracked files stayed outside the proposal and the workspace was unchanged. |
| PR drafts and human checkpoints | `b9685a1` | Validated the Delivery document from a live isolated check. Accepted a review signed for the exact proposal and rejected an implementation grant as a review. Publication stayed disabled. |

The local suite with Docker enabled reported **209 passed, 3 skipped**. Ruff lint, formatting, and the diff check passed. Hosted CI awaits publication.

`prepare_delivery()` produces proposals and draft PR text. The trusted host can use `review_digest()` and `review_progress()` to confirm an ordered prefix of signed reviews. A review confirms the proposal and does not record a Git commit, publish to GitHub, or apply files to the shared checkout. Performing and reconciling those actions is a separate authorized workflow. M7 awaits a new assignment.

---

# 12. M7 — Integrated Skill-Driven Workflow

**Priority:** High  
**Status:** Verified for the local workflow

**Depends on:** M1–M6

### 12.1 Objective

Integrate the AEW skill layer with the deterministic engine into a coherent engineering workflow.

### 12.2 Initial integration

The first integrated skill is:

`aew/skills/aew-task/SKILL.md`

It should orchestrate:

- Task intake.
- Repository identification.
- Preflight.
- Context retrieval.
- Planning.
- Approval requests.
- Execution handoff.
- Verification.
- Delivery preparation.

The skill must not bypass engine authorization.

### 12.3 Stable interfaces

The engine should expose a small, stable interface suitable for AI coding environments.

Possible interface forms include:

- Local CLI commands.
- Structured JSON input/output.
- Process-level tool integration.

A network service is not required for the initial implementation.

The exact interface should be selected based on the simplest demonstrable integration.

### 12.4 End-to-end scenarios

At minimum, test:

**Scenario A — Quick bug fix**

A localized defect with clear acceptance criteria.

**Scenario B — Standard feature**

A feature spanning multiple related files.

**Scenario C — Deep change**

A cross-cutting change requiring dependency analysis.

**Scenario D — Explore**

An investigation that produces findings without modifying code.

**Scenario E — Interrupted execution**

A task suspended and resumed after repository state changes.

### 12.5 Exit criteria

M7 is verified when:

- The skill can invoke the engine through stable interfaces.
- Tasks progress through valid states.
- Context and authorization remain consistent.
- Read-only and write workflows are clearly separated.
- Checkpoints survive interruption.
- Delivery artifacts are traceable.
- Real engineering tasks can be completed without bypassing safety boundaries.

### 12.6 Verification record

| Work Unit | Commit | Observed result |
|---|---|---|
| JSON task intake | `1f8a9b1` | Exercised all four profiles through the CLI, validated exported Task documents, and confirmed the advisory gate for incomplete preflight. |
| Trusted workflow handoff | `68b0158` | Exercised read-only Explore, denied isolated work for unresolved preflight, rejected resume after workspace drift, and resumed after revalidation. Ran an isolated check through the host and produced a schema-valid delivery draft and signed review. |
| Skill integration | This documentation commit | Connected the task skill to the JSON CLI and trusted handoff, and verified the documented module command against the real repository. |

The full local suite with Docker enabled reported **214 passed, 3 skipped**. Ruff lint and formatting passed. A read-only Explore intake on shared `master` at `53ad6c6` returned `awaiting_approval` with an investigation request and left the checkout unchanged.

The isolated implementation scenario used mocked remote observations and real Git, SQLite, Docker, and signed host checks. Authenticated live GitHub CLI verification remains open from M1. The skill documents the local interface and trust boundary. Trusted host provisioning and publication remain separately authorized. Hosted CI awaits publication. M8 awaits a new assignment.

---

# 13. M8 — Hardening and Pilot Adoption

**Priority:** Medium  
**Status:** Planned  
**Depends on:** M7

### 13.1 Objective

Validate AEW against representative engineering projects and refine its usability, performance, and reliability.

### 13.2 Pilot environments

Use several repository types to validate portability.

Suggested categories:

- Small Python service.
- Java application.
- Go service.
- PHP application.
- Mixed-language repository.
- Legacy modernization project.

These are test environments, not mandatory framework integrations.

### 13.3 Performance evaluation

Measure:

- Time to useful preflight.
- Context retrieval latency.
- Project Brain update cost.
- Unnecessary rediscovery.
- Planning overhead.
- Execution interruptions.
- Verification coverage.
- Human intervention frequency.

Avoid optimizing based on synthetic benchmarks alone.

### 13.4 Reliability evaluation

Test:

- Dirty worktrees.
- Conflicting PRs.
- Stale context.
- Revoked grants.
- Invalid execution envelopes.
- Interrupted processes.
- Concurrent file changes.
- Partial tool failures.
- Missing external services.
- Corrupted or inconsistent local state.

### 13.5 Exit criteria

M8 is verified when:

- AEW performs reliably on multiple project types.
- Safety invariants survive negative testing.
- Routine tasks do not incur excessive ceremony.
- Project knowledge improves subsequent work.
- Documentation reflects operational behavior.
- The system demonstrates practical engineering value.

---

# 14. Cross-Cutting Engineering Requirements

These requirements apply to every milestone.

## 14.1 Contract-first boundaries

Use explicit contracts between major components.

Avoid tightly coupling AI skill behavior to internal engine implementation details.

## 14.2 Fail-safe behavior

When safety-relevant evidence is unavailable:

- Do not assume success.
- Preserve the current workspace.
- Report the missing evidence.
- Request intervention when required.

## 14.3 Deterministic enforcement

Security-sensitive checks must be enforced by code, not solely by prompts or instructions.

## 14.4 Observability

Record enough information to explain:

- What was requested.
- What was observed.
- What was authorized.
- What was executed.
- What was verified.
- Why execution stopped.

Avoid logging secrets unnecessarily.

## 14.5 Idempotency

Where practical, repeated operations should avoid duplicating state changes.

Checkpoint recovery and knowledge reconciliation must account for retries.

## 14.6 Compatibility

Changes to versioned contracts must be reviewed for backward compatibility.

Breaking changes require explicit versioning and migration decisions.

## 14.7 Documentation synchronization

Changes affecting contracts, public interfaces, or architectural behavior must update relevant documentation.

Planned features must not be presented as completed.

---

# 15. Testing Strategy

Testing is organized into layers.

| Layer | Purpose |
|---|---|
| Contract | JSON Schema validity and fixture rejection |
| Semantic | Cross-contract consistency |
| Unit | Pure logic and component behavior |
| Integration | Git, SQLite, filesystem behavior |
| Adapter | External CLI and API error handling |
| End-to-end | Complete engineering workflows |
| Security | Unauthorized operations and boundary violations |
| Recovery | Checkpointing, interruption, and resumption |

### 15.1 Mandatory negative tests

Safety-sensitive components must demonstrate rejection of invalid conditions.

Examples:

- Unauthorized operation.
- Expired approval.
- Revoked approval.
- Plan revision mismatch.
- Repository mismatch.
- Protected path modification.
- Symlink escape.
- Concurrent file modification.
- Stale context.
- Incomplete PR enumeration.
- Branch collision.
- Workspace overlap without safe handling.

### 15.2 Evidence requirements

A milestone may only be marked verified when its acceptance criteria have been demonstrated through reproducible tests or documented manual verification.

Assertions such as "the tests should pass" do not constitute evidence.

---

# 16. Dependency and Sequencing Rules

### 16.1 Required ordering

The following dependencies must be preserved:

- Contract validation before controlled execution.
- Repository preflight before implementation.
- Project Brain snapshots before Context Package generation.
- Context Package identity before execution binding.
- Plan revision before approval binding.
- Authorization before restricted operations.
- Guarded filesystem operations before AI-driven modifications.
- Verification before claiming delivery readiness.
- Publication authorization before Git publication.

### 16.2 Parallel development

Parallel work is acceptable when components have stable interfaces.

Examples:

- GitHub adapter testing alongside Project Brain schema design.
- Contract documentation alongside unit testing.
- Project intelligence detection alongside SQLite persistence.

Parallel work must not introduce conflicting assumptions about shared contracts.

### 16.3 Avoid premature infrastructure

Do not introduce:

- A distributed message broker.
- A central orchestration server.
- A graph database service.
- A plugin marketplace.
- A complex agent scheduler.
- A general-purpose workflow DSL.

Such infrastructure should be considered only when demonstrated requirements justify it.

---

# 17. Release Strategy

The following release grouping is suggested.

| Release | Target capability |
|---|---|
| v0.1 | Verified read-only repository/task preflight |
| v0.2 | Persistent Project Brain and Context Packages |
| v0.3 | Adaptive planning and authorization |
| v0.4 | Controlled execution and checkpointing |
| v0.5 | Verification and delivery preparation |
| v0.6 | Integrated workflows and pilot hardening |

Release numbers are indicative and may change.

Milestone exit criteria are more important than calendar dates or version labels.

---

# 18. Immediate Implementation Backlog

The next engineering actions, in priority order, are:

1. Materialize and audit existing drafted source files.
2. Establish project metadata and test dependencies.
3. Execute the existing contract tests.
4. Correct confirmed contract inconsistencies.
5. Execute configuration and Git adapter tests.
6. Harden Git porcelain parsing.
7. Execute local preflight tests.
8. Add GitHub client tests.
9. Restrict GitHub CLI command execution.
10. Implement remote/local baseline reconciliation.
11. Build a complete read-only preflight report.
12. Demonstrate the first end-to-end read-only workflow.

No controlled execution or publication functionality should be added until the foundational safety and authorization requirements are ready.

---

# 19. Roadmap Governance

This document is a living implementation plan.

### 19.1 When to update

Update the roadmap when:

- A milestone is completed.
- A significant dependency changes.
- A milestone is split or consolidated.
- An implementation approach changes materially.
- A newly identified risk affects sequencing.
- An accepted ADR changes the implementation strategy.

### 19.2 What requires architectural review

Changes to the following require review against accepted ADRs:

- Project Brain consistency model.
- Knowledge provenance.
- Context Package immutability.
- Authorization boundaries.
- Workspace protection.
- Execution scope.
- Checkpoint semantics.
- Git publication defaults.
- Work Unit delivery boundaries.

### 19.3 What does not normally require a new ADR

Routine implementation choices such as:

- Internal helper functions.
- Local refactoring.
- Test organization.
- Non-breaking internal interfaces.
- Performance optimizations preserving behavior.
- Minor tooling improvements.

Do not create ADRs for ordinary implementation details.

---

# 20. Definition of Success

AEW succeeds when it improves engineering throughput without reducing control, understanding, or confidence.

A successful implementation should demonstrate:

- Less repeated repository investigation.
- Persistent and trustworthy project knowledge.
- Planning proportional to task complexity.
- Clear authorization boundaries.
- Protection of unrelated work.
- Recoverable long-running execution.
- Evidence-backed verification.
- Reviewable Work Unit delivery.
- Predictable Git publication behavior.

The system should remain useful for a small bug fix while scaling to larger architectural work.

**AEW's central engineering principle remains:**

**Reason adaptively. Preserve knowledge. Enforce deterministically. Verify with evidence. Deliver deliberately.**

---

# 21. Codex Implementation Directive

When using this roadmap in Codex:

1. Read `AGENTS.md`, `docs/architecture.md`, and relevant accepted ADRs.
2. Inspect the repository before making changes.
3. Establish which files and capabilities actually exist.
4. Begin with M0 unless a later milestone has already been verified.
5. Implement one coherent vertical slice at a time.
6. Run relevant tests after each change.
7. Report blockers and contract inconsistencies explicitly.
8. Preserve unrelated workspace modifications.
9. Do not silently alter accepted architectural decisions.
10. Do not execute Git publication without explicit authorization.
11. Update documentation to match verified implementation behavior.
12. Stop at the agreed milestone boundary and present evidence before proceeding.

**Initial target: M0 — Repository Bootstrap and Verification Baseline.**

The first implementation handoff should produce a verified baseline, a list of confirmed defects, and a proposed sequence for completing M1.

Do not begin autonomous execution development as part of the initial handoff.
