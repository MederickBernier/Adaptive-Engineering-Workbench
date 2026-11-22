# AGENTS.md — Adaptive Engineering Workbench

**Project:** Adaptive Engineering Workbench (AEW)  
**Architecture baseline:** v0.1  
**Instructions version:** 0.1.0

## 1. Project Identity

AEW is a local-first, skill-first hybrid AI-assisted engineering workbench.

It combines:

- AI skills for adaptive reasoning, investigation, planning, and implementation guidance.
- A deterministic local engine for validation, persistence, authorization, guarded execution, and verification.
- A persistent, project-specific knowledge system called the Project Brain.
- Git and GitHub awareness for repository preflight and coordination.
- Adaptive Work Units for reviewable implementation and delivery.

The engineer retains authority over architectural decisions and restricted operations.

**Core principle: Reason adaptively. Preserve knowledge. Enforce deterministically. Verify with evidence. Deliver deliberately.**

## 2. Documentation and Decision Authority

Read documentation proportionally to the task.

### Required entry points

- `README.md` — Project overview.
- `docs/architecture.md` — Approved architecture.
- `docs/implementation-roadmap.md` — Milestones and acceptance criteria.
- `docs/codex-handoff.md` — Current implementation assignment.
- `docs/adr/README.md` — Architecture Decision Record index.
- `contracts/*.schema.json` — Versioned interface contracts.

Read relevant individual ADRs before changing the components or invariants they govern.

### Authority rules

- Accepted ADRs establish architectural decisions.
- Versioned contracts establish structural interfaces.
- Repository security policies and explicit authorization govern restricted operations.
- The roadmap defines implementation sequence, not permission to execute.
- Existing source code is evidence of current implementation, not proof of architectural correctness.
- Examples and historical notes are informative unless explicitly adopted as normative.

If documents conflict, identify the conflict and report it. Do not silently choose the interpretation that makes implementation easiest.

No document overrides applicable security policy or authorization requirements.

## 3. Current Implementation Boundary

The initial implementation assignment is:

**M0 — Repository Bootstrap and Verification Baseline**

See `docs/codex-handoff.md`.

During M0, focus on:

- Repository inventory.
- Development environment setup.
- Contract validation.
- Existing engine verification.
- Unit and integration testing.
- Confirmed defect correction.
- Minimal CI setup.
- Accurate documentation.

Do not begin later milestones without a new assignment.

The current Python engine is provisional. Do not treat Python as a permanent architectural requirement.

## 4. Mandatory Engineering Workflow

For each assigned task:

1. **Inspect** — Establish repository state, relevant source, tests, and existing changes.
2. **Understand** — Read applicable contracts and ADRs.
3. **Scope** — Define the smallest coherent change boundary.
4. **Plan** — Use a proportional plan based on risk and uncertainty.
5. **Authorize** — Verify the active instructions and required permissions.
6. **Implement** — Modify only the approved scope.
7. **Verify** — Run relevant tests and inspect results.
8. **Review** — Examine the diff for unrelated or unintended changes.
9. **Document** — Update documentation affected by actual behavior changes.
10. **Report** — Summarize changes, evidence, limitations, and remaining work.

Do not convert routine maintenance into unnecessary specification ceremonies.

For small, low-risk changes, a concise plan is sufficient.

For architectural, security-sensitive, or cross-cutting changes, provide a more detailed analysis before implementation.

## 5. Repository Safety

Before modifying files:

- Inspect Git status.
- Identify staged, unstaged, and untracked changes.
- Preserve unrelated modifications.
- Confirm the intended file scope.
- Avoid overwriting concurrent changes.
- Do not assume the current branch is suitable for implementation.
- Do not assume remote-tracking references are current.

Never run destructive Git commands to simplify workspace state.

In particular, do not use `git reset --hard`, `git clean -fd`, or force-push as a workaround for unrelated changes.

Do not create or switch branches without appropriate authorization.

If workspace consistency cannot be established, stop the affected operation and report the uncertainty.

## 6. Architectural Invariants

### 6.1 Project Brain

- Knowledge assertions are immutable.
- Snapshots are revision-scoped and coherent.
- Snapshot membership is explicit.
- Knowledge must retain provenance.
- Freshness and investigation depth are independent.
- Durable and derived knowledge remain logically distinct.
- Stale derived knowledge must not be presented as current fact.

Relevant ADRs: ADR-003, ADR-006, ADR-007, ADR-008.

### 6.2 Context Packages

- Context Packages are immutable.
- Package identity and integrity must be verifiable.
- Repository revision and Project Brain snapshot must be explicit.
- Evidence and uncertainties must remain traceable.
- Expanding context must not mutate an existing package.
- Incompatible revision contexts must not be silently combined.

Relevant ADR: ADR-009.

### 6.3 Preflight and Workspace Consistency

- Preflight is required before implementation.
- Local-only inspection cannot establish complete remote clearance.
- Missing evidence must not be treated as success.
- Dirty worktrees require scope-aware assessment.
- Non-overlapping paths do not guarantee semantic independence.
- File modifications require concurrency protection.

Relevant ADRs: ADR-004, ADR-005.

### 6.4 Planning and Work Units

- Planning depth must be proportional to risk and uncertainty.
- Supported profiles are Quick, Standard, Deep, and Explore.
- Plans are revisioned.
- Work Units represent meaningful engineering boundaries.
- Material scope changes require approval reassessment.

Relevant ADRs: ADR-011, ADR-012.

### 6.5 Authorization and Execution

- AI reasoning is not authorization.
- Configuration is not authorization.
- A schema-valid grant is not proof of trusted approval.
- Restricted operations require valid, scoped authorization.
- Protected paths take precedence over allowed paths.
- Execution budgets must be enforced.
- Budget exhaustion must suspend execution.
- Checkpoint resumption requires revalidation.

Relevant ADR: ADR-010.

### 6.6 Verification and Delivery

- Test success requires observed evidence.
- Unavailable verification must be reported explicitly.
- One proposed commit per meaningful Work Unit is the default.
- Stage, commit, push, PR creation, and merge are disabled by default.
- Preparing delivery artifacts does not authorize publication.

Relevant ADR: ADR-011.

## 7. Implementation Standards

Prefer:

- Small, cohesive modules.
- Explicit interfaces and contracts.
- Strong typing.
- Fail-fast validation.
- Deterministic behavior.
- Clear error handling.
- Dependency injection where useful.
- Tests focused on observable behavior.
- Minimal dependencies.
- Incremental vertical slices.

Avoid:

- Speculative abstractions.
- Premature framework creation.
- Unnecessary infrastructure.
- Hidden global state.
- Broad refactoring unrelated to the task.
- Reimplementing AI reasoning as rigid engine logic.
- Treating prompts as security enforcement.

Use the existing project conventions where they are compatible with accepted architecture.

## 8. Contract and Test Discipline

AEW contracts use JSON Schema Draft 2020-12.

The primary contracts are:

- `contracts/task.schema.json`
- `contracts/context.schema.json`
- `contracts/approval.schema.json`
- `contracts/execution.schema.json`
- `contracts/delivery.schema.json`

Validation must distinguish:

1. Structural schema validity.
2. Cross-contract semantic consistency.
3. Runtime authority and state enforcement.

Do not treat these as interchangeable.

When changing a contract:

- Identify affected consumers.
- Assess compatibility.
- Update fixtures.
- Update relevant tests.
- Update documentation.
- Request review for breaking changes.

Negative tests are required for safety-sensitive behavior.

Do not weaken tests solely to make the suite pass.

## 9. External Tools and Dependencies

Use external tools deliberately.

### Git

Use Git-native validation for Git reference semantics.

Repository inspection should be read-only unless a specific modification is authorized.

### GitHub

Use explicit repository identity.

Treat remote API responses as external data.

Handle authentication failures, pagination, timeouts, and incomplete responses.

Do not interpret missing remote information as evidence that no conflicts exist.

### Dependencies

Prefer standard-library functionality when adequate.

Do not add major dependencies or infrastructure without a demonstrated requirement.

Do not install global tools or alter developer-wide configuration without permission.

## 10. Verification Requirements

After implementation:

- Run the most relevant tests.
- Run broader regression tests when warranted.
- Inspect the resulting diff.
- Confirm unrelated changes were preserved.
- Report actual test commands and outcomes.
- Identify skipped or unavailable checks.
- State remaining uncertainty.

Never claim that code was tested when tests were not executed.

A passing test suite is evidence of tested behavior, not proof of complete system correctness.

## 11. Documentation Maintenance

Update documentation when behavior, contracts, or architecture change.

Use:

- `README.md` for project orientation.
- `docs/architecture.md` for consolidated architecture.
- `docs/implementation-roadmap.md` for milestone sequencing.
- `docs/codex-handoff.md` for current assignment boundaries.
- `docs/adr/` for architectural decisions.
- Contract schemas for machine-readable interface definitions.

Do not create a new ADR for routine implementation details.

Do not silently modify an accepted ADR.

If a decision must change, propose a new ADR or an explicitly reviewed superseding decision.

## 12. Prohibited Autonomous Actions

Unless explicitly authorized for the current task, do not:

- Stage files.
- Execute commits.
- Push branches or tags.
- Create or modify pull requests.
- Merge pull requests.
- Rewrite Git history.
- Delete unrelated files.
- Modify protected repository paths.
- Install global dependencies.
- Change repository security policies.
- Expand the assigned milestone.
- Execute destructive repository operations.

The existence of a roadmap, contract, or approval example does not grant these permissions.

## 13. Stop and Escalation Conditions

Stop the affected operation and request guidance when:

- An accepted ADR conflicts with the proposed implementation.
- A breaking contract change is required.
- Repository identity or expected baseline is uncertain.
- Unrelated changes cannot be preserved safely.
- Required authorization is missing.
- A security boundary cannot be enforced.
- A major technology or infrastructure decision is required.
- The assigned milestone has reached its completion gate.

Ordinary test failures may be investigated and corrected within the authorized scope.

Avoid repeated speculative fixes without evidence.

## 14. Required Completion Report

At the end of each assigned Work Unit or milestone, report:

- Objective and scope.
- Files created or modified.
- Implementation summary.
- Tests executed and observed results.
- Unverified or unavailable checks.
- Remaining defects and risks.
- Proposed commit title and body.
- Documentation updates.
- Milestone or Work Unit completion status.

Do not execute the proposed commit unless explicitly authorized.

## 15. Final Operating Rule

AEW is intended to improve engineering effectiveness without uncontrolled autonomy.

Codex should preserve architectural decisions, maintain engineering clarity, enforce scope, and provide evidence of completed work.

**Implement the smallest coherent capability that satisfies the current assignment, verify it, report the result, and stop at the agreed boundary.**