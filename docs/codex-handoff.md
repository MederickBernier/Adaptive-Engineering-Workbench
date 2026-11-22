# Adaptive Engineering Workbench (AEW)
# Codex Implementation Handoff

**Document:** `docs/codex-handoff.md`  
**Version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Status:** Initial implementation handoff  
**Last updated:** 2026-11-22  
**Initial authorized milestone:** M0 — Repository Bootstrap and Verification Baseline

---

## 1. Purpose

This document defines the operational handoff from AEW's architecture and design phase to implementation using Codex.

It establishes:

- The project's purpose and engineering philosophy.
- The authoritative documentation and decision hierarchy.
- The expected initial repository state.
- The scope of Codex's first assignment.
- The boundaries Codex must respect.
- The verification evidence required.
- The conditions under which implementation must stop for review.

This document is intended to be read alongside `AGENTS.md`, `docs/architecture.md`, `docs/implementation-roadmap.md`, and the relevant Architecture Decision Records.

It is not a replacement for those documents.

**The initial objective is to establish a verified implementation baseline, not to implement the entire AEW platform.**

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

Before beginning M0, inspect:

- `AGENTS.md`, if present.
- `README.md`.
- `docs/architecture.md`.
- `docs/implementation-roadmap.md`.
- `docs/adr/README.md`, if present.
- `contracts/*.schema.json`.
- Relevant existing source and tests.

Read individual ADRs when their decisions affect the current Work Unit.

Do not assume missing documentation exists.

### 3.3 Missing ADRs

The architecture baseline includes accepted decisions ADR-003 through ADR-012.

Their individual Markdown documents may not yet exist in the repository.

ADR-001 and ADR-002 have not been independently confirmed for this handoff.

Codex must:

- Report missing ADR documents.
- Preserve established decisions where documented.
- Avoid inventing historical rationale.
- Avoid treating proposed reconstructions as accepted decisions.
- Request review before changing an established invariant.

Missing documentation does not automatically authorize architectural redesign.

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

The intended initial repository layout is:

```text
aew/
├── AGENTS.md
├── README.md
├── docs/
│   ├── architecture.md
│   ├── implementation-roadmap.md
│   ├── codex-handoff.md
│   └── adr/
│       └── README.md
├── skills/
│   └── aew-task/
│       └── SKILL.md
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
    │   ├── test_config.py
    │   └── test_preflight.py
    └── integration/
        └── test_git_repository.py
```

This structure describes the planned baseline.

It is not proof that every file exists.

Codex must inspect the actual filesystem and report differences.

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

## 16. Initial Codex Assignment

The following instruction may be used directly when starting the Codex implementation session.

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
- M0 is confirmed as the initial milestone.

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