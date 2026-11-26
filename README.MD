# Adaptive Engineering Workbench (AEW)

**A local-first, skill-driven engineering workbench for AI-assisted software development.**

**Status:** Early development — v0.1.0  
**Architecture:** v0.1 baseline approved  
**Implementation:** Skill-first hybrid  
**License:** To be determined

> AEW helps developers use AI on existing and new software projects while preserving engineering knowledge, architectural constraints, Git safety, and human control over consequential decisions.

## Overview

Adaptive Engineering Workbench (AEW) is an engineering orchestration system designed to integrate AI coding assistants into practical software development workflows.

AEW combines lightweight agent skills with a local engine responsible for project knowledge, task coordination, authorization, execution evidence, and Git delivery safeguards.

The system is designed to support both small changes in existing repositories and larger engineering efforts, including greenfield projects, debugging, refactoring, architectural investigations, and feature development.

AEW is **not intended to replace engineering judgment or impose a rigid software development methodology**.

Its objective is to reduce repetitive work while keeping important engineering decisions explicit, verifiable, and reviewable.

## Core Principles

1. **Human authority:** AI agents operate within explicitly authorized boundaries.
2. **Adaptive workflows:** Planning and verification effort scale with task risk, uncertainty, and complexity.
3. **Evidence over assumptions:** Engineering knowledge must retain provenance and verification status.
4. **Repository awareness:** Agents must understand source revisions, existing work, and relevant dependencies.
5. **Knowledge reuse:** Verified findings should remain available for future tasks without requiring repeated discovery.
6. **Safe execution:** Existing developer changes and repository policies must be respected.
7. **Controlled delivery:** Commit messages and PR descriptions are prepared automatically; publication is disabled by default.
8. **Minimal overhead:** Documentation, approvals, and task decomposition must provide concrete engineering value.
9. **Language neutrality:** AEW discovers each project's technologies and conventions rather than imposing a preferred stack.
10. **Incremental improvement:** Features and complexity are introduced only when justified by actual requirements.

## Architecture

AEW follows a **Skill-First Hybrid** architecture.

### Engineering Skills

Skills provide AI agents with task-specific procedures and interaction contracts.

The initial skill is:

- `aew-task` — Repository-aware task analysis, Git preflight, knowledge retrieval, classification, and implementation planning.

Planned skills include:

- `aew-investigate` — Evidence-backed debugging and investigation.
- `aew-implement` — Controlled implementation of approved Work Units.
- `aew-review` — Review against requirements, contracts, and verification evidence.
- `aew-deliver` — Commit proposal and pull request preparation.

Skills guide agent behavior. They are not, by themselves, security enforcement mechanisms.

### AEW Core Engine

The local engine is responsible for operations that require authoritative state or enforceable controls.

Its planned responsibilities include:

- Task and Work Unit coordination.
- Repository and GitHub integration.
- Project Brain storage and retrieval.
- Approval grant validation.
- Execution scope enforcement.
- Workspace integrity protection.
- Verification evidence collection.
- Durable execution checkpoints.
- Commit and PR delivery coordination.

The engine is planned as a modular local application, not a collection of independent microservices.

### Project Brain

Each project has a local, SQLite-backed Project Brain.

The Project Brain stores and retrieves evidence-backed knowledge about a repository, including:

- Project languages, frameworks, and tooling.
- Components and dependencies.
- Applicable conventions and architectural contracts.
- Source-derived assertions.
- Discovery coverage and freshness.
- Task-relevant historical findings.

Knowledge is scoped to repository revisions and snapshots.

Assertions must not be silently combined across incompatible source revisions.

Discovery is progressive: AEW begins with lightweight repository understanding and deepens its knowledge around relevant components as tasks require.

The Project Brain logically separates durable operational state from rebuildable derived knowledge.

The MVP proposes a single SQLite database per project, although the physical layout is not an architectural requirement.

### Shared Engineering Knowledge

AEW also supports a Git-backed, Markdown-based engineering knowledge vault.

The vault is intended for reusable patterns, procedures, architectural principles, and engineering lessons.

Project-specific or confidential knowledge must respect its visibility boundaries and must not be automatically promoted into a shared knowledge base.

Use `aew-task vault validate --vault <directory>` to validate Markdown in a dedicated Git vault directory. Commit the notes before validating. The command reads regular Markdown files from Git HEAD, including nested directories. Use `--commit <full-sha>` to select another local revision.

Each Markdown file in that directory is a managed note. Start it with YAML frontmatter containing `id`, `title`, `status`, `kind`, `visibility`, `created`, `updated`, and `sources`. Use stable `kb:<namespace>:<identifier>` IDs and a nonempty list of sources with `type` and `value`. Relationships such as `related` and `supersedes` resolve by ID within the same revision. Full vault synchronization and promotion are outside this read-only workflow.

Use `aew-task vault search --vault <directory> --query "retry operations"` to find active, shared notes. Omit `--query` to list them. Use `aew-task vault show --vault <directory> kb:engineering:idempotent-operations` to read a note with its provenance, applicability, Git commit, and blob ID. Both commands accept `--commit <full-sha>`. Keep restricted notes in separately access-controlled repositories. Vault results are reference material, and task intake does not load them automatically.

## Workflow

AEW uses four adaptive task profiles:

| Profile | Purpose |
|---|---|
| Quick | Bounded changes with low uncertainty |
| Standard | Moderate features, bugs, and refactors |
| Deep | Architectural, cross-cutting, or high-risk work |
| Explore | Investigation and evidence gathering without implicit implementation authority |

A typical workflow is:

1. Receive a GitHub issue or natural-language task.
2. Inspect repository state and perform read-only Git preflight.
3. Retrieve relevant Project Brain knowledge.
4. Classify the task and prepare a proportional plan.
5. Resolve material uncertainty and obtain scoped authorization.
6. Execute approved Work Units within enforced boundaries.
7. Run appropriate verification and record evidence.
8. Prepare a commit proposal for each completed Work Unit.
9. Prepare a pull request title and description.
10. Leave publication to the developer unless separately authorized.

A Work Unit is a meaningful, reviewable change—not every internal implementation step.

Small tickets normally require only one Work Unit.

## Git and Delivery Policy

AEW is designed to integrate with existing team Git workflows.

### Branches

New task branches originate from the latest verified integration baseline.

Branch naming is configurable.

Example:

`mb/fix/142-token-refresh`

The prefix, naming pattern, and integration branch may be configured at user or project level.

Preflight must inspect relevant branches, pull requests, workspace changes, and potential dependencies before implementation.

### Commits

By default, AEW:

- Prepares one commit proposal per completed Work Unit.
- Provides a commit title and body.
- Identifies the intended change boundary.
- Includes relevant verification evidence.
- Preserves unrelated developer modifications.
- Does not stage or execute commits automatically.

Sequential commit checkpoints are the initial mechanism for preserving Work Unit boundaries.

### Pull Requests

AEW prepares a PR title and description based on actual changes and recorded verification.

By default, AEW does not push branches, create pull requests, or merge changes.

These operations require separate authorization or applicable configuration, subject to repository policy.

## Contracts

AEW uses versioned JSON Schema contracts to define boundaries between skills, the core engine, and engineering operations.

The initial contract set uses **JSON Schema Draft 2020-12**.

| Contract | File | Responsibility |
|---|---|---|
| Task | `contracts/task.schema.json` | Task identity, assessment, evidence, planning, and Work Units |
| Context | `contracts/context.schema.json` | Revision-scoped knowledge, provenance, freshness, and limitations |
| Approval | `contracts/approval.schema.json` | Scoped authorization grants and permitted operations |
| Execution | `contracts/execution.schema.json` | Bounded execution, workspace expectations, verification, and budgets |
| Delivery | `contracts/delivery.schema.json` | Commit proposals, change boundaries, PR preparation, and publication state |

### Contract Boundaries

**Task Contract:** Describes what needs to be accomplished. It does not authorize execution.

**Context Contract:** Describes what is known and the evidence supporting it. It does not grant permissions.

**Approval Contract:** Describes authorized operations. Grants must be validated against trusted engine state and repository policy.

**Execution Contract:** Binds a Work Unit to its approved scope, workspace, context, verification requirements, and execution budget.

**Delivery Contract:** Records prepared Git deliverables and observed publication states. A delivery record cannot authorize its own publication.

JSON Schema provides structural validation. Semantic requirements—including source consistency, authorization authenticity, filesystem protection, and Git state verification—must be enforced by the engine.

## Security and Safety

AEW distinguishes two operating modes:

| Mode | Description |
|---|---|
| Advisory | Skills guide an agent; enforcement depends on the surrounding agent environment |
| Controlled | Modifying operations pass through guarded AEW tooling or an equivalent enforceable isolation boundary |

Advisory mode must never be presented as providing guaranteed execution isolation.

The controlled engine must validate permissions independently of model instructions.

Important safeguards include:

- Protected integration branches.
- Explicit authorization for modifying operations.
- Scope-aware workspace checks.
- Concurrent file modification detection.
- Protected paths and canonical path validation.
- No unauthorized Git publication.
- Traceable verification results.
- Durable execution checkpoints.
- Project knowledge visibility restrictions.

## Repository Structure

The initial target structure is:

```text
aew/
├── README.md
├── skills/
│   └── aew-task/
│       └── SKILL.md
├── contracts/
│   ├── task.schema.json
│   ├── context.schema.json
│   ├── approval.schema.json
│   ├── execution.schema.json
│   └── delivery.schema.json
├── engine/
├── tests/
└── docs/
    └── architecture.md
```

Directories and files are introduced incrementally as implementation requires them.

This structure is a target, not a claim that all components are already implemented.

## MVP Roadmap

The complete v0.1 MVP will be developed through incremental vertical slices.

| Increment | Deliverable |
|---|---|
| v0.1.0 | Initial skill, contracts, and read-only task intake |
| v0.1.1 | Persistent, revision-aware Project Brain |
| v0.1.2 | Controlled investigation and implementation |
| v0.1.3 | Commit proposals and PR drafting |
| v0.1.4 | Recovery, integration testing, and pilot instrumentation |

### MVP Acceptance Scenario

Given a real GitHub issue, AEW must be able to:

1. Understand the issue and relevant repository context.
2. Perform Git and PR preflight.
3. Prepare an appropriately scoped plan.
4. Obtain and validate execution authorization.
5. Complete an authorized Work Unit safely.
6. Record actual verification evidence.
7. Prepare reviewable commit and PR artifacts.
8. Avoid unauthorized publication and preserve existing developer work.

The MVP must also handle stale knowledge, dirty workspaces, overlapping PRs, interrupted execution, and failed verification.

## Evaluation

AEW is intended to be evaluated against real engineering work, not only successful demonstrations.

Initial safety targets are:

- Zero unauthorized repository modifications.
- Zero lost developer changes.
- Zero unauthorized Git publication operations.
- All reported verification outcomes traceable to execution evidence.

Productivity and usability measurements will include task completion time, review rework, retrieval usefulness, manual interventions, and developer feedback.

Performance improvements must be demonstrated through representative tasks rather than assumed.

## Current Development Status

The v0.1 prototype includes JSON task intake, revision-scoped Project Brain knowledge, Context Packages, advisory planning, guarded isolated execution, and delivery drafts. The M8 local pilot exercised four representative fixture types and the AEW checkout. The Python implementation remains provisional. Hosted verification for M8 and authenticated live GitHub CLI verification are tracked in the roadmap.

## Architecture Decisions

The following architectural decisions are approved:

| ADR | Decision |
|---|---|
| ADR-003 | Snapshot Consistency |
| ADR-004 | Workspace Consistency |
| ADR-005 | Branch Preflight and Configurable Naming |
| ADR-006 | Project Intelligence Profile |
| ADR-007 | Discovery and Invalidation |
| ADR-008 | Progressive Discovery and Retrieval Budgets |
| ADR-009 | Context Package |
| ADR-010 | Execution Contract |
| ADR-011 | Delivery Contract |
| ADR-012 | Planning and Approval Policy |

The Knowledge Contract and Project Brain architectural decisions are also approved.

Implementation details may evolve without reopening these decisions, provided their guarantees remain satisfied.

## Documentation Maintenance Policy

AEW documentation is maintained incrementally alongside implementation.

### Source of Truth

- `README.md` — Project overview, current capabilities, onboarding, and roadmap.
- `docs/architecture.md` — Approved architecture, boundaries, invariants, and design decisions.
- `contracts/*.schema.json` — Machine-readable contract structures.
- `skills/*/SKILL.md` — Agent-facing skill procedures.
- Tests — Executable evidence of supported behavior.

### Change Requirements

When a Work Unit changes documented behavior, its delivery must include the corresponding documentation updates.

Examples:

| Change | Documentation to review |
|---|---|
| New user-facing command | README and command documentation |
| Contract structure change | Schema, examples, and relevant architecture references |
| New or modified skill | Skill documentation and README |
| Architectural decision | Architecture specification and ADR register |
| Configuration change | Configuration reference and examples |
| New implemented capability | README development status and roadmap |
| Safety policy change | Relevant contracts, architecture documentation, and tests |

Documentation updates should be included in the same Work Unit whenever practical.

**Do not create documentation tasks merely to satisfy a ceremony.** Update documentation when the engineering change makes existing information incomplete or inaccurate.

### Documentation Quality Rules

Documentation must distinguish:

- Implemented behavior.
- Approved but not yet implemented behavior.
- Proposed or experimental behavior.
- Known limitations.

Examples must be consistent with the current contract schemas.

Changes to an approved architectural invariant require an explicit amendment and impact assessment.

Documentation should explain the system's contracts and behavior without duplicating implementation details unnecessarily.

## Contributing

AEW is currently in early development.

Use Python 3.13 and Git to work on the prototype. From the repository root, create a virtual environment and install the engine and development tools.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check engine tests
.\.venv\Scripts\python.exe -m ruff format --check engine tests
```

On macOS or Linux, use `.venv/bin/python` for commands after creating the virtual environment. The Git integration tests use disposable local repositories. Live GitHub client calls require the GitHub CLI.

GitHub Actions runs these checks on Linux and Windows for pushes to `master` and pull requests targeting it.

To include pull request evidence in Python preflight, construct `GitPreflight` with `github=GitHubClient("owner/repository")` for the selected github.com Git remote. Use an authenticated GitHub CLI that supports `gh api --paginate --slurp` and `gh pr view --json closingIssuesReferences`. Incomplete enumeration leaves pull request coordination unverified.

Pass `verify_remote=True` to `GitPreflight.inspect()` to observe the integration HEAD and, with `git.branches.check_remote_collision` enabled, check the proposed branch against live refs. `remote_branch_collision` is `False` only when the live lookup confirms the branch is absent. A failed or skipped lookup leaves it unset.

Preflight reports `BLOCKED` for known blockers and `UNAVAILABLE` when required evidence is missing. With complete baseline, branch, workspace scope, and pull request evidence, it reports `WARNING` for advisory findings or `PASSED` when there are none. These results are observations for review and grant no permission to modify the workspace.

Until then, the approved architecture and versioned contracts define the project's intended behavior.

## Project Brain

Use one SQLite file per local checkout. Keep it outside the tracked repository, and bind it to the checkout's resolved root URI.

```python
from pathlib import Path

from engine.brain.discovery import discover
from engine.brain.retrieval import retrieve
from engine.brain.store import ProjectBrain
from engine.git.repository import GitRepository

repository = GitRepository(Path.cwd())
brain = ProjectBrain(Path.home() / "aew-project-brain.sqlite3", repository.root.as_uri())
snapshot = discover(repository, brain, regions=("engine", "tests"))

# After opening the same database in a later session
snapshot_ids = brain.snapshot_ids(snapshot.revision.commit)
historical = brain.load(snapshot_ids[0])
view = retrieve(repository, brain, historical.id, target_commit=repository.head_commit())
```

Discovery reads a committed Git tree. Omit `regions` for broad discovery, or pass literal repository-relative paths for targeted discovery. Use a full commit ID to inspect a historical revision. The built-in detectors record D0 existence and D1 structure from recognized files. Investigators can publish evidence-backed D2 and D3 assertions through `ProjectBrain.publish()`. Verification status and investigation depth are preserved when a claim becomes stale.

Retrieval separates current and stale claims. A changed region or an explicit `depends_on` assertion can invalidate previously applicable knowledge. Published snapshots remain available for historical retrieval, and a missing claim means the available snapshot has no evidence for it.

---

## Adaptive planning

Call `assess()` with observed risk, uncertainty, and a rationale to recommend Quick, Standard, Deep, or Explore. `build_plan()` accepts that assessment, a task, and the relevant Context Package and preflight report. Quick can generate one Work Unit from the task acceptance criteria and verification checks. Supply explicit units with dependencies for Standard or Deep. Explore records investigation questions, stopping checks, and a budget.

Use `PlanHistory(brain).append(draft)` to publish revision 1 in the checkout's Project Brain. Pass `expected_revision=1` to revise it, and use `load(plan_id, revision)` to retrieve a specific historical record. Opening a version 1 Project Brain adds the plan history table while preserving existing snapshots. Revision records identify material changes and approval checkpoints. The v0.1 Task document remains exportable, and its approval state describes requests only.

---

## Isolated execution

The trusted host issues signed grants and exposes the supported execution adapters. Bind each operation to its Work Unit, Context Package, Git baseline, expected file versions, and budget.

`IsolatedChecks` prepares approved text changes and runs a named verification command recorded in the Work Unit. The host supplies an absolute Docker executable, a local Linux image pinned by ID, and the allowed command. The disposable checkout contains committed text files and the reviewed changes, excludes protected files, and uses no host mounts or external network. Review the returned diff separately. Applying that diff to the shared checkout requires explicit authorization.

To run the opt-in Docker integration tests, set `AEW_TEST_DOCKER_IMAGE` to the ID of a locally installed image with Python 3.13 at `/usr/local/bin/python`, then run pytest. The standard suite skips those two tests when the variable is unset.

---

## Task workflow

From an attached checkout, send task intake JSON to the installed `aew-task` command or to `python -m engine.workflow.cli`. AEW creates a checkout-specific database under `%LOCALAPPDATA%\AEW\projects` on Windows or `$XDG_DATA_HOME/aew/projects` on Unix (defaulting to `~/.local/share/aew/projects`). Use `--brain` to select an existing database outside the checkout.

```powershell
Get-Content task.json -Raw | aew-task
```

Run `aew-task config show` for a read-only JSON report of config files, recognized settings and their sources, the Brain path, and the integration branch hint. Use `--repository` or `--brain` with this command to inspect the same paths you would use for intake.

Example `task.json` for Quick planning:

```json
{
  "task": {
    "id": "example-fix",
    "objective": "Clarify the CLI help text",
    "acceptance": ["Help describes the required database path"]
  },
  "assessment": {
    "risk": "low",
    "uncertainty": "low",
    "rationale": "The edit is limited to a help message.",
    "localized": true,
    "acceptance_clear": true
  },
  "approach": "Update the help message and check the command output.",
  "task_type": "fix",
  "region": "engine/workflow",
  "scope": ["engine/workflow/cli.py"],
  "verification": ["Inspect the CLI help output"]
}
```

The JSON response contains the sealed Context Package and recorded plan revision. Preserve both for the trusted host. Remote verification is opt-in through `--verify-remote` and `--github-repository owner/repository`. With no configured integration branch, local inspection uses the cached remote HEAD as a hint and remote verification queries the live symbolic HEAD. AEW's own `.aew/config.json` keeps `master` and `mb/` project-specific. An unresolved preflight can produce an advisory implementation plan. Isolated execution requires complete preflight coverage and a scoped grant. The trusted host exposes the guarded operations through `TaskHost`.

---

## First-time Project Brain setup

Run `aew-task bootstrap --repository <checkout>` to scan the committed tree and print a JSON draft with evidence and maintainer questions. The scan excludes working-tree changes and leaves the Project Brain database untouched.

Use these commands for an interactive first-time setup. Add `--repository <checkout>` when working outside the target checkout.

```text
aew-task bootstrap start
aew-task bootstrap show --session <id>
aew-task bootstrap answer --session <id> --expect <version> --question ownership --maintainer "Name" --answer "The billing team owns this service."
aew-task bootstrap publish --session <id> --review-digest <digest>
```

The `aew-task` skill uses the draft to guide the interview. Use the version returned by the last command when recording each response, or run `show` to resume. Use `--disposition skipped` or `--disposition deferred` in place of `--answer` when appropriate. Maintainer names are supplied by the operator and recorded as attribution. Once all questions have a disposition, review the draft and approve its digest before publication. Deferred questions are preserved as uncertainties in the local Project Brain.

Routine intake reuses an approved bootstrap snapshot for the same commit. An explicitly selected snapshot takes precedence, and intake falls back to scoped discovery when no approved bootstrap snapshot exists for the commit.

## Local pilot

From the source checkout, run `python -m scripts.pilot_m8` to measure intake and Project Brain reuse on disposable Python, Java, Go, and mixed Python/TypeScript repositories. Add `--repository <attached-checkout>` to include a real repository read-only. The script uses temporary databases and prints timings and observations as JSON. See the [M8 verification record](docs/implementation-roadmap.md#136-verification-record) for measured results and limits.

---

## Project Direction

AEW aims to make AI-assisted engineering more reliable, context-aware, and practical without removing developers from architectural and delivery decisions.

The long-term goal is a reusable engineering workbench that can operate across different languages, frameworks, repositories, and AI coding environments while preserving the standards and workflows of each project.

**Build incrementally. Verify behavior. Preserve engineering control.**
