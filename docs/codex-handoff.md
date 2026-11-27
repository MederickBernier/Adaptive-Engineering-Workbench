# Adaptive Engineering Workbench (AEW)
# Codex Implementation Handoff

**Document:** `docs/codex-handoff.md`  
**Version:** 0.1.1

**Architecture baseline:** AEW v0.1 with accepted orchestration extension

**Status:** Documentation acceptance and alignment

**Last updated:** 2026-11-26

**Historical initial milestone:** M0 — Repository Bootstrap and Verification Baseline

---

## 0. Current Assignment and Milestone State

### 0.1 Authorized documentation Work Unit

The engineer accepted ADR-013 through ADR-017 on 2026-11-26 and authorized documentation updates to record that acceptance and align the architecture, roadmap, ADR registry, and this handoff. Authorized edits are limited to Markdown documentation. Completion requires consistency, local-link, file-scope, and historical-evidence preservation checks and a proposed commit description.

The accepted ADRs govern future design and implementation. Future runtime, schema, dependency, and execution changes require a separately assigned Work Unit with applicable contract review and authorization.

### 0.2 Completed baseline and historical material

The [roadmap](implementation-roadmap.md) records the completed M0–M8 sequence and its observed limitations.

| Milestones | Recorded status |
|---|---|
| M0–M4 | Verified |
| M5 | Verified for isolated execution |
| M6 | Verified for delivery preparation |
| M7 | Verified for the local workflow |
| M8 | Verified for the local pilot |

External adoption and other verification gaps retain their individual recorded status. Sections 4–16 preserve historical initial-handoff procedures and the M0 verification record. Section 16 contains the historical M0 kickoff. The current assignment is defined in section 0.1.

### 0.3 Future implementation entry point

The next planned implementation milestone is M9 — Delegation Contracts and Sandbox Eligibility, followed by M10 — Specialist Runtime and Result Packages, M11 — Adaptive Orchestration and Hierarchical Budgets, M12 — Controlled Reconciliation and Integration, and M13 — Multi-Agent Hardening and Pilot Evaluation. Scope and exit criteria are in roadmap section 22.

After a separate M9 assignment, begin with repository and consumer inventory, compatibility and migration review of existing contracts, and a bounded runtime-evidence approval design. Review breaking schema changes with the engineer before implementation. Preserve the existing milestone evidence and supported behavior of current callers.

### 0.4 Accepted extension requirements

- Route every specialist launch, including provider-native subagents, through the engine. Use versioned roles and composable specialization labels with immutable assignment bindings.
- Require explicit delegation permission, validated child authority records, and permission intersections with parent authority, profile, assignment, runtime, and policy.
- Admit runtimes using versioned isolation capabilities, observed verification evidence, and a trusted evidence approval record. Withdrawal blocks affected operations and triggers evidence reassessment.
- Enforce finite resource, concurrent-agent, and cumulative launch limits. Failed provisioning and fresh replacement attempts consume launch allowance. Duplicate request delivery counts once. Live or uncertain runtimes retain concurrent reservations until termination is established.
- Validate the complete combined diff, including integration-generated changes, before verification or review and again before application. Successful required checks and accepted required reviews bind to the exact immutable candidate.
- Give reviewers and verifiers candidate-specific immutable context with explicit rebinding on observation changes. Establish applicability to the actual target commit before publishing candidate findings as current committed-revision knowledge.
- Apply a reviewed candidate only with current application authorization, preflight, workspace concurrency checks, and a confirmed resulting change boundary. Preserve unrelated changes and reconcile uncertain outcomes before retry.

The current five schemas provide existing interfaces. New contracts, authority records, candidate bindings, and runtime eligibility controls are future implementation work governed by the accepted ADRs and M9 contract review.

---

## 1. Purpose

This document defines the operational handoff from AEW's architecture and design phase to implementation using Codex.

It establishes:

- The project's purpose and engineering philosophy.
- The authoritative documentation and decision hierarchy.
- The expected initial repository state.
- The current documentation assignment and the retained initial implementation assignment.
- The boundaries Codex must respect.
- The verification evidence required.
- The conditions under which implementation must stop for review.

This document is intended to be read alongside `AGENTS.md`, `docs/architecture.md`, `docs/implementation-roadmap.md`, and the relevant Architecture Decision Records.

It is not a replacement for those documents.

The current objective is documentation acceptance and alignment of the orchestration extension. The original M0 objective and verification evidence remain part of the historical handoff.

---

## 2. Project Identity

### 2.1 Name

Adaptive Engineering Workbench (AEW)

### 2.2 Mission

AEW is a local-first, skill-first hybrid AI-assisted engineering system.

It combines AI reasoning with deterministic enforcement to support repository investigation, project knowledge management, adaptive planning, controlled implementation, verification, and delivery preparation.

The system must improve engineering productivity without sacrificing human understanding, repository integrity, or explicit authorization.

### 2.3 Core principle

**Reason adaptively. Preserve knowledge. Enforce deterministically. Verify with evidence. Deliver deliberately.**

### 2.4 Architectural model

AEW consists of two primary layers.

**AI Skill Layer**

Responsible for adaptive reasoning, task interpretation, investigation, planning, implementation guidance, and delivery preparation.

**Deterministic Engine Layer**

Responsible for contract validation, repository inspection, persistent state, authorization, guarded operations, execution budgets, checkpoints, and verification records.

The AI layer may propose actions.

The engine must enforce the boundaries governing those actions.

The accepted orchestration extension adds engine-mediated specialist assignments, versioned role profiles, verified sandbox eligibility, delegated authority records, and controlled integration of immutable result packages. Implementation follows the future M9–M13 sequence.

### 2.5 Initial implementation technology

Python is the provisional implementation language for the current prototype.

It was selected for the initial drafted modules and test harness, not as a permanent architectural commitment.

Codex must not reinterpret this provisional choice as a decision to build all future AEW components in Python.

Any proposal to change the engine language or substantially alter the implementation strategy must be presented for review.

---

## 3. Documentation Authority

Codex must distinguish architectural requirements from implementation guidance.

### 3.1 Authority hierarchy

When documents conflict, apply the following order:

1. Explicit current instructions and authorizations from the engineer.
2. Accepted Architecture Decision Records and their invariants.
3. Approved architecture and versioned contracts.
4. Repository security and operational policies.
5. Implementation roadmap.
6. This handoff document.
7. Existing implementation and tests.
8. Historical notes, examples, and provisional drafts.

This hierarchy does not permit overriding repository security policy through a casual instruction.

Security-sensitive operations must satisfy all applicable policy and authorization requirements.

### 3.2 Required documents

Before beginning an assigned Work Unit, inspect:

- `AGENTS.md`, if present.
- `README.md`.
- `docs/architecture.md`.
- `docs/implementation-roadmap.md`.
- `docs/adr/README.md`, if present.
- `contracts/*.schema.json`.
- Relevant existing source and tests.

Read individual ADRs when their decisions affect the current Work Unit.

Do not assume missing documentation exists.

### 3.3 ADR availability and status

The repository contains ADR-001 through ADR-017. ADR-003 through ADR-012 form the confirmed original baseline. ADR-013 through ADR-017 were accepted on 2026-11-26 as the orchestration extension. ADR-001 and ADR-002 retain their pre-existing acceptance-history ambiguity. See the [ADR index](adr/README.MD).

### 3.4 Conflict handling

When source code, tests, contracts, and architecture disagree:

1. Identify the conflicting artifacts.
2. Explain the precise inconsistency.
3. Determine whether the issue is structural, semantic, behavioral, or architectural.
4. Propose the smallest correction preserving approved invariants.
5. Request review if the correction changes a public contract or architectural decision.
6. Record the resolution.

Do not silently rewrite an accepted contract to make a failing test pass.

---

## 4. Expected Repository Structure

The M0 repository layout includes:

```text
AEW repository/
├── AGENTS.MD
├── README.MD
├── pyproject.toml
├── .gitignore
├── .github/workflows/ci.yml
├── docs/
│   ├── architecture.md
│   ├── implementation-roadmap.md
│   ├── codex-handoff.md
│   └── adr/
│       └── README.MD
├── aew/
│   └── skills/
│       └── aew-task/
│           └── SKILL.md
├── contracts/
│   ├── task.schema.json
│   ├── context.schema.json
│   ├── approval.schema.json
│   ├── execution.schema.json
│   ├── delivery.schema.json
│   └── examples/
├── engine/
│   ├── config.py
│   ├── git/
│   │   ├── repository.py
│   │   └── preflight.py
│   └── github/
│       └── client.py
└── tests/
    ├── contracts/
    │   ├── test_schemas.py
    │   └── test_semantics.py
    ├── unit/
    │   ├── test_unit.py
    │   ├── test_github_client.py
    │   └── test_preflight.py
    └── integration/
        └── test_git_repository.py
```

The verification record in section 13.7 documents the inspected baseline and remaining gaps.

### 4.1 Source availability

During the design phase, source files and documentation were drafted individually in conversation.

Some or all may need to be copied into the repository.

Codex must not claim a missing file was inspected or tested.

If required source content is unavailable, request the source or permission to reconstruct it from the approved specification.

Do not fabricate successful verification results for absent files.

---

## 5. Initial Assignment

### 5.1 Milestone

**M0 — Repository Bootstrap and Verification Baseline**

Reference: `docs/implementation-roadmap.md`

### 5.2 Objective

Establish a reproducible development environment and verify the existing drafted foundation.

The result should be a working baseline suitable for implementing M1.

### 5.3 Authorized work scope

Codex may, subject to the engineer's active instructions and repository permissions:

- Inspect repository contents.
- Inspect Git status and existing changes.
- Inspect architecture and contracts.
- Identify missing files.
- Configure development tooling.
- Add necessary Python package metadata.
- Add or correct tests.
- Correct localized implementation defects.
- Improve error handling.
- Add documentation required for reproducible setup.
- Propose contract corrections.
- Prepare a verification report.

This document alone does not grant write access.

The engineer's actual Codex session permissions and instructions govern which modifications may be performed.

### 5.4 Excluded work

Do not implement during M0:

- Project Brain persistence.
- Context Package generation.
- Adaptive planning orchestration beyond existing drafts.
- Authorization grant issuance.
- Guarded source-code execution.
- Automated task branch creation.
- Automated commits.
- Git pushes.
- Pull request publication.
- Pull request merging.
- Autonomous multi-agent orchestration.

Do not begin M1 implementation merely because M0 appears straightforward.

---

## 6. Required Initial Repository Audit

Before modifying source files, Codex must establish the repository's actual state.

### 6.1 Git inspection

Inspect:

- Repository root.
- Current branch.
- HEAD commit.
- Staged changes.
- Unstaged changes.
- Untracked files.
- Existing branches relevant to the task.

Do not perform a Git fetch, checkout, reset, clean, rebase, or branch creation as part of the initial audit.

### 6.2 Source inventory

Determine which expected files exist.

Classify each relevant artifact as:

- Present and inspectable.
- Present but incomplete.
- Missing.
- Conflicting with documentation.
- Unverified.

### 6.3 Dependency inventory

Identify:

- Python version.
- Git version.
- GitHub CLI availability.
- Existing project metadata.
- Test dependencies.
- Existing linting and formatting tools.
- Existing CI workflows.

Do not install global dependencies without authorization.

Prefer project-local, reproducible tooling.

### 6.4 Baseline report

Before substantial changes, produce a concise report containing:

- Repository state.
- Available implementation.
- Missing assets.
- Existing tests.
- Known inconsistencies.
- Proposed M0 changes.
- Risks to unrelated work.

If the repository contains unrelated modifications, preserve them and identify any overlap with the proposed changes.

---

## 7. M0 Implementation Sequence

Execute M0 incrementally.

### Step 1 — Establish package structure

Ensure the Python prototype can be imported and tested consistently.

Add package markers or packaging metadata where required.

Avoid unnecessary packaging frameworks.

### Step 2 — Establish development dependencies

Use the smallest practical dependency set.

Expected initial development tools include:

- pytest.
- jsonschema.
- A formatter and linter, if selected.
- Standard Python tooling.

Do not introduce runtime dependencies merely for convenience when the standard library is sufficient.

### Step 3 — Validate JSON contracts

Inspect and validate:

- Task Contract.
- Context Package Contract.
- Approval Contract.
- Execution Contract.
- Delivery Contract.

Validate schema definitions against JSON Schema Draft 2020-12.

Run positive and negative fixtures.

Ensure negative fixtures fail for the intended reason rather than an unrelated defect.

### Step 4 — Validate cross-contract semantics

Test consistency between:

- Task identifiers.
- Plan revisions.
- Work Unit references.
- Context Package identifiers.
- Snapshot identifiers.
- Approval Grant references.
- Workspace identity.
- Repository identity.
- Delivery references.

Semantic validation functions intended for production must eventually reside in engine code rather than only in tests.

Do not prematurely create a large validation framework.

### Step 5 — Verify configuration management

Inspect `engine/config.py`.

Verify:

- Default configuration.
- User configuration precedence.
- Project configuration precedence.
- Branch naming.
- Invalid configuration handling.
- Publication defaults.

Ensure ordinary configuration cannot be interpreted as an authorization grant.

### Step 6 — Verify Git adapter

Inspect `engine/git/repository.py`.

Run disposable-repository integration tests.

Test:

- Repository discovery.
- Clean and dirty worktrees.
- Staged and unstaged changes.
- Untracked files.
- Renames and copies.
- Detached HEAD.
- Branch enumeration.
- Git-native branch validation.
- Unusual filenames.
- Local remote-tracking references.

Correct confirmed porcelain parsing defects.

### Step 7 — Verify local preflight

Inspect the latest version of `engine/git/preflight.py`.

The drafted latest revision is v0.1.1.

Verify:

- Conservative scope matching.
- Unsupported pattern rejection.
- Workspace overlap classification.
- Branch proposal.
- Known branch collision reporting.
- Missing integration baseline handling.
- Incomplete preflight reporting.

Local-only preflight must not claim full repository clearance.

### Step 8 — Verify GitHub adapter

Inspect `engine/github/client.py`.

Add isolated tests using mocked CLI responses.

Test:

- Valid issue responses.
- Valid PR responses.
- Authentication failure.
- CLI unavailability.
- Timeouts.
- Malformed JSON.
- Invalid commit identifiers.
- Pagination boundaries.
- Missing fields.
- Incomplete changed-file information.
- Unexpected command requests.

No real GitHub account or network access should be required for ordinary unit tests.

### Step 9 — Establish continuous integration

Add a minimal CI workflow covering:

- Contract validation.
- Unit tests.
- Disposable Git integration tests.
- Static analysis.
- Formatting checks.

CI must not require production credentials.

### Step 10 — Produce M0 verification report

Summarize:

- Changes made.
- Tests executed.
- Results.
- Remaining defects.
- Contract concerns.
- Known limitations.
- Readiness for M1.

Stop after this report.

---

## 8. Known Technical Risks

The following risks were identified during the design phase.

They are investigation targets, not assumptions that the code is defective in every environment.

### 8.1 Git porcelain parsing

The initial Git adapter decodes NUL-delimited porcelain output as text.

Potential problems include unusual filenames and filesystem encoding behavior.

Prefer byte-oriented parsing with filesystem-compatible decoding.

Verify rename and copy ordering against actual Git output.

### 8.2 Configuration validation

The initial configuration implementation does not fully reject unknown keys or validate all enumerated settings.

Strengthen validation without introducing unnecessary configuration complexity.

### 8.3 Scope parsing

The local preflight parser was revised to reject unsupported scope expressions.

Verify the revision is present.

Lexical overlap analysis must not be reused as filesystem write authorization.

### 8.4 GitHub CLI restrictions

The initial GitHub adapter has a command allowlist that should be narrowed.

Only explicitly supported read-only operations should be callable.

The public adapter methods must not accidentally expose arbitrary API requests.

### 8.5 GitHub pagination

The initial implementation detects some incomplete PR enumerations.

It does not yet guarantee completeness of unusually large PR file lists.

Do not treat incomplete file data as proof of non-overlap.

### 8.6 Remote freshness

Local remote-tracking references may be stale.

Remote GitHub observations and local Git observations must be reconciled before claiming the latest verified integration baseline.

This belongs primarily to M1.

### 8.7 Read-only Execution Envelope

The initial Execution Contract requires:

`delivery.prepare_commit = true`

This conflicts with a pure read-only investigation workflow.

Codex should document the conflict and propose a versioned correction.

Do not silently weaken the contract.

### 8.8 Fixture consistency

Some fixtures represent different stages of a fictional task.

They are not necessarily one coherent execution history.

Tests must distinguish independent schema validity from end-to-end workflow consistency.

### 8.9 Authorization provenance

Approval JSON is data, not proof of user authorization.

Future runtime authorization must validate trusted grant issuance and current authority.

M0 must not introduce a shortcut that treats a self-declared active grant as sufficient.

---

## 9. Non-Negotiable Invariants

The following rules must remain true throughout implementation.

### 9.1 Repository safety

- Preserve unrelated changes.
- Do not overwrite concurrent modifications.
- Do not assume a clean worktree.
- Do not treat path non-overlap as semantic independence.
- Do not modify files outside authorized scope.

### 9.2 Knowledge consistency

- Preserve revision-scoped snapshots.
- Keep assertions immutable.
- Track provenance.
- Separate freshness from investigation depth.
- Preserve uncertainty.
- Do not silently mix incompatible revisions.

### 9.3 Context integrity

- Context Packages are immutable.
- Context identity is verifiable.
- Evidence is traceable.
- Expanded context does not mutate the original package.

### 9.4 Authorization

- AI instructions do not replace authorization.
- Configuration does not replace authorization.
- A valid schema does not establish authority.
- Grants are bound to task, plan, repository, workspace, and scope.
- Revoked or expired grants cannot authorize execution.

### 9.5 Execution

- Execution remains within the authorized envelope.
- Protected paths take precedence.
- Unexpected workspace changes trigger safe handling.
- Budget exhaustion suspends execution.
- Checkpoint resumption requires revalidation.

### 9.6 Delivery

- Work Units define meaningful delivery boundaries.
- One proposed commit per meaningful Work Unit is the default.
- Staging and committing are disabled by default.
- Pushing, PR creation, and merging are disabled by default.
- Verification claims require evidence.

---

## 10. Testing and Verification Policy

### 10.1 Test categories

Use:

- Contract tests.
- Semantic tests.
- Unit tests.
- Integration tests.
- Mocked external-adapter tests.
- Security-negative tests where relevant.

### 10.2 Test evidence

Every verification report should identify:

- Test command.
- Execution environment.
- Result.
- Relevant failure details.
- Whether the result was observed or inferred.

### 10.3 Failure handling

When tests fail:

1. Identify the failing assertion.
2. Determine whether the implementation or test expectation is incorrect.
3. Check the relevant contract and ADR.
4. Apply the smallest appropriate correction.
5. Rerun affected tests.
6. Report remaining failures.

Do not weaken tests solely to obtain a passing result.

### 10.4 Unavailable tests

If a test cannot execute:

- Mark it unavailable.
- Explain why.
- Identify the missing dependency or environment condition.
- Do not report it as passed.

---

## 11. Change Management

### 11.1 Allowed routine changes

Within the approved M0 scope, routine corrections may include:

- Fixing imports.
- Correcting implementation bugs.
- Adding missing tests.
- Improving error messages.
- Removing unnecessary duplication.
- Correcting inaccurate implementation documentation.
- Adding minimal packaging configuration.

These remain subject to the engineer's active permissions.

### 11.2 Changes requiring review

Request review before:

- Changing accepted ADRs.
- Breaking versioned contracts.
- Changing Project Brain consistency semantics.
- Changing Context Package immutability.
- Weakening authorization.
- Expanding execution permissions.
- Introducing unrestricted shell access.
- Changing Git publication defaults.
- Introducing major dependencies or infrastructure.
- Replacing the implementation language.

### 11.3 Work Unit discipline

Prefer one coherent change boundary at a time.

Do not bundle unrelated refactoring into a defect correction.

Prepare meaningful summaries and proposed commit messages.

Do not execute commits unless explicitly authorized.

---

## 12. Codex Operating Workflow

Codex should use the following operational sequence.

```text
Receive assignment
        |
        v
Read AGENTS.md and relevant documentation
        |
        v
Inspect repository and Git state
        |
        v
Identify existing implementation
        |
        v
Identify applicable ADRs and contracts
        |
        v
Produce bounded implementation plan
        |
        v
Confirm required authorization
        |
        v
Implement within approved scope
        |
        v
Run relevant verification
        |
        v
Inspect resulting diff
        |
        v
Update documentation
        |
        v
Report results and unresolved issues
        |
        v
STOP at milestone boundary
```

If the repository changes unexpectedly during implementation, re-evaluate the affected assumptions before continuing.

---

## 13. Required M0 Handoff Report

At the end of M0, Codex must provide a structured report.

### 13.1 Repository baseline

- Repository path.
- Branch.
- Initial HEAD.
- Initial workspace state.
- Existing unrelated changes.

### 13.2 Implementation inventory

- Files inspected.
- Files created.
- Files modified.
- Missing planned files.
- Deferred components.

### 13.3 Verification

| Check | Command | Result | Evidence |
|---|---|---|---|
| Schema validation | Actual command | Pass/Fail/Unavailable | Actual result |
| Semantic validation | Actual command | Pass/Fail/Unavailable | Actual result |
| Configuration tests | Actual command | Pass/Fail/Unavailable | Actual result |
| Git integration | Actual command | Pass/Fail/Unavailable | Actual result |
| Preflight tests | Actual command | Pass/Fail/Unavailable | Actual result |
| GitHub adapter tests | Actual command | Pass/Fail/Unavailable | Actual result |
| Static analysis | Actual command | Pass/Fail/Unavailable | Actual result |

Do not populate the results with anticipated outcomes.

### 13.4 Remaining issues

Classify unresolved issues as:

- Blocking.
- Important.
- Deferred.

Include affected files and relevant architectural decisions.

### 13.5 Proposed delivery

Provide:

- Summary of changes.
- Proposed Work Unit boundaries.
- Proposed commit titles and bodies.
- Remaining verification gaps.
- Recommendation for M1 readiness.

### 13.6 Final milestone status

Use one of:

- **Verified:** All M0 exit criteria demonstrated.
- **Partially verified:** Some criteria demonstrated, with explicit gaps.
- **Blocked:** A dependency or defect prevents completion.

---

### 13.7 M0 verification record

**Status:** Verified on 2026-11-22. The audited workstation checkout was `F:/Skills Development/AI Engineering Workbench` on `master` at `13d40a8`. The initial working tree was clean.

| Work Unit | Commit | Result |
|---|---|---|
| Development environment | `1acefab` | Added Python package metadata, editable installation, pytest and Ruff configuration, and setup instructions. |
| Contract verification | `a3e9733` | Added the Standard task fixture and corrected the negative approval fixture filename. |
| Local engine verification | No change required | Verified configuration, Git integration, and local preflight with 73 passing tests. |
| GitHub client | `7f1d165` | Added 13 offline tests and made malformed response fields raise `GitHubDataError`. |
| CI | `7434bc4` | Added the Linux and Windows jobs and aligned the Python source and developer commands with Ruff. |

The audit covered the four engine modules, all five schemas, their fixtures, the test modules, the task skill, and the architecture documents. Configuration tests are in `tests/unit/test_unit.py`. All twelve ADR files are present.

| Check | Command | Observed result |
|---|---|---|
| Clean Python 3.13 environment | `python -m venv .venv`, then `python -m pip install -e ".[dev]"` in that environment | Editable installation succeeded. |
| Draft 2020-12 schemas, fixtures, and cross-contract semantics | `python -m pytest -q -p no:cacheprovider tests/contracts` | 27 passed, 3 skipped. Both negative fixtures failed for their intended reasons. |
| Configuration, local preflight, and disposable Git integration | `python -m pytest -q tests/unit tests/integration` at the local engine checkpoint | 73 passed. |
| Mocked GitHub CLI | `python -m pytest -q tests/unit/test_github_client.py` | 13 passed. |
| Full test suite | `python -m pytest -q` using the local virtual environment | 113 passed, 3 skipped. The skipped cases are negative-fixture checks for contracts without negative examples. |
| Static analysis and formatting | `python -m ruff check engine tests` and `python -m ruff format --check engine tests` | Both passed. |
| Hosted verification | [GitHub Actions run 45018923750](https://github.com/MederickBernier/Adaptive-Engineering-Workbench/actions/runs/45018923750) | The workflow completed successfully for `7434bc4` with the Linux and Windows matrix. |

The Windows sandbox blocked Git's shell during a disposable local-remote test. The full suite passed outside the sandbox.

| Classification | Remaining issue |
|---|---|
| Important | ADR-001 and ADR-002 have conflicting acceptance language. Confirm their decision history with the engineer before relying on either record as accepted. |
| Deferred | The Execution schema requires `delivery.prepare_commit: true`. Read-only Explore support requires the reviewed, versioned contract change specified in [ADR-010](adr/ADR-010-controlled-execution.md). |
| Deferred | Live GitHub adapter calls and complete remote preflight remain unverified. The current suite exercises mocked GitHub responses and disposable local Git repositories. M1 owns remote preflight integration. |

The verified baseline is ready for M1 review. M1 requires a new assignment.

## 14. Stop Conditions

Codex must stop and request review when:

- A required architectural decision is ambiguous.
- A proposed correction would violate an accepted ADR.
- A versioned contract requires a breaking change.
- Required authorization is unavailable.
- Existing workspace changes cannot be preserved safely.
- Repository identity or expected baseline cannot be established.
- A restricted operation would exceed approved scope.
- A major dependency or infrastructure decision is required.
- M0 reaches its milestone boundary.

A test failure does not automatically require stopping if a correction is clearly within the approved scope.

However, repeated speculative fixes without evidence are not acceptable.

---

## 15. M0 Completion Gate

M0 is complete only when:

- The repository structure has been audited.
- Required source files are available or missing assets are explicitly reported.
- The development environment is reproducible.
- JSON Schemas have been validated.
- Positive and negative fixtures have been exercised.
- Cross-contract tests have been executed.
- Configuration tests have been executed.
- Git integration tests have been executed.
- Local preflight tests have been executed.
- GitHub adapter tests have been added and executed.
- Known defects have been corrected or documented.
- CI has been established.
- Documentation matches verified behavior.
- The final M0 report has been delivered.

If any requirement remains unmet, M0 must be reported as partially verified or blocked.

**Codex must not begin M1 automatically.**

---

## 16. Historical Initial Codex Assignment

The following instruction records the original M0 kickoff for historical reference. The current assignment is in section 0.1.

### Assignment: AEW M0 — Bootstrap and Verification

You are implementing the Adaptive Engineering Workbench (AEW), a local-first, skill-first hybrid AI-assisted engineering system.

Your assignment is limited to **Milestone M0 — Repository Bootstrap and Verification Baseline**.

Read the repository's `AGENTS.md`, `README.md`, `docs/architecture.md`, `docs/implementation-roadmap.md`, and relevant accepted ADRs.

Inspect the existing repository before making modifications.

Establish which drafted source files and contracts are actually present. Do not assume missing files exist.

Produce a concise initial audit identifying the current repository state, available implementation, missing assets, test infrastructure, and known architectural inconsistencies.

Then establish a reproducible Python prototype environment, execute the existing tests, correct confirmed defects within the approved scope, and add missing baseline tests where appropriate.

Preserve unrelated workspace changes.

Do not change accepted architectural decisions or breaking contracts without review.

Do not implement Project Brain persistence, controlled execution, authorization issuance, or Git publication during M0.

Do not stage, commit, push, create pull requests, or merge without explicit authorization.

At completion, provide:

- Repository audit.
- Summary of modifications.
- Test commands and observed results.
- Remaining defects and risks.
- Proposed commit boundaries.
- M0 completion status.
- Recommendation for beginning M1.

**Stop after M0 and wait for the engineer's review.**

---

## 17. Handoff Acceptance

This handoff is accepted for implementation when:

- The engineer has supplied the relevant repository.
- The authoritative documents are available.
- The implementation scope is understood.
- Required permissions are established.
- Codex can inspect the existing source.
- The engineer has explicitly assigned the selected documentation Work Unit or implementation milestone.

This document does not itself constitute permission to modify files or publish repository changes.

---

## 18. Final Directive

AEW is intended to provide engineering acceleration without uncontrolled autonomy.

Implementation must preserve the distinction between:

- Reasoning and enforcement.
- Knowledge and evidence.
- Planning and authorization.
- Execution and verification.
- Delivery preparation and publication.

Favor small, verifiable improvements over large speculative implementations.

**The first success criterion is not the amount of code generated. It is establishing a trustworthy engineering foundation on which subsequent capabilities can be built.**
