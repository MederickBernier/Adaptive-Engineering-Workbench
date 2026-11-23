
# Adaptive Engineering Workbench (AEW)
## Architecture Specification v0.1

**Status:** Approved architecture baseline; repository reference (v0.1)  
**Baseline:** v0.1 (2026-11-21)  
**Audience:** Maintainers, developers, AI integration implementers, reviewers  
**Canonical format:** Markdown in version control

> This document consolidates decisions approved during design. Example schemas and command names are illustrative unless expressly identified as contractual. Implementation details left open by the design freeze remain open.

## 1. Purpose and success criterion

AEW is a local-first, human-governed engineering workbench supporting small bug fixes, features, greenfield development, and long-running analysis. It combines project-specific knowledge retrieval with bounded AI-assisted execution. It must improve engineering throughput without replacing developer judgment or creating mandatory specification ceremonies.

**Primary MVP scenario:** Given a GitHub issue or natural-language task, AEW identifies the repository and relevant knowledge, performs read-only preflight, proposes proportional planning, obtains scoped authorization, supports implementation and verification, prepares a commit proposal for each completed Work Unit, and prepares a PR title/body **without staging, committing, pushing, opening a PR, or merging by default**.

**Non-goals for v0.1:** autonomous deployment/merge, distributed knowledge services, cross-repository graph federation, vector search, full Obsidian synchronization, complex patch queues, and multi-agent orchestration.

## 2. Architectural principles

1. **Human authority:** AI knowledge and advice do not grant permissions. Explicitly authorized scopes govern modifying actions.
2. **Evidence before assertion:** Important project facts carry provenance, verification state, and source-revision applicability.
3. **Adaptive effort:** Planning and discovery scale with risk, uncertainty, and the affected dependency frontier—not repository size alone.
4. **Local-first:** Each project has a local SQLite-backed Project Brain; shared knowledge is managed in Git-backed Markdown.
5. **Separation of concerns:** Git is authoritative for source, GitHub for issue/PR state, approved documents for policy, and the Project Brain for indexed/retrieved knowledge and operational state.
6. **No silent publication:** Preparation is distinct from staging, committing, pushing, PR creation, and merging.
7. **Recoverability:** Execution can be reconstructed from durable checkpoints and observed evidence.
8. **Repository neutrality:** Language, frameworks, and conventions are discovered from each project rather than imposed globally.

## 3. Decision register

| ADR | Decision | Status |
|---|---|---|
| 003 | Snapshot consistency: coherent revision-scoped graph and immutable assertions | Approved |
| 004 | Workspace consistency: scope-aware dirty-worktree and concurrent-write protection | Approved |
| 005 | Branch preflight and configurable naming namespace | Approved, including amendment |
| 006 | Project intelligence profile and project-specific convention discovery | Approved |
| 007 | Staged discovery and targeted invalidation | Approved |
| 008 | Progressive discovery and retrieval budgets | Approved |
| 009 | Context Package contract | Approved |
| 010 | Scoped Execution Envelope and evidence-backed verification | Approved, reviewed version |
| 011 | Work Units, commit proposals, and PR delivery | Approved |
| 012 | Adaptive planning and event-driven approval | Approved |

Additional approved foundations: one SQLite-backed Project Brain per project; assertion-based knowledge graph; logical separation of durable and derived knowledge; Git-backed Obsidian-compatible Markdown knowledge vault with stable IDs, typed relations, provenance, visibility boundaries, and provisional AI inferences.

## 4. Logical system architecture

```text
Developer / ChatGPT / IDE Agent
             |
    AEW Skills (agent guidance)
             |
    AEW Core (local engine)
   +---------+----------+------------------+
   |         |          |                  |
 Task Router |    Policy & Execution  Delivery Coordinator
             |
       Project Brain
   +---------+------------------------------+
   |                                        |
SQLite (durable state + derived graph)   Git-backed knowledge vault
   |
Adapters: Git, GitHub (gh), source discovery, test runners, AI
```

These are **logical responsibilities**, not mandatory microservices or processes. The approved implementation direction is **skill-first hybrid**: small agent-facing skills call a local AEW engine for trusted state, preflight, evidence, and guarded operations. The first vertical slice is a read-only `aew-task` skill. The engine is a single modular local application, not a fleet of services. Implementation language and API transport remain undecided.

**Enforcement distinction:** advisory skills can guide an external agent but cannot guarantee restrictions when that agent has direct write or shell access. Controlled mode requires guarded operations or equivalent sandbox isolation; policy claims must match the actual enforcement boundary.

### 4.1 Responsibilities

- **Task Router:** Resolve issue/request; establish intent and acceptance; classify Quick, Standard, Deep, or Explore; identify material questions and Work Units.
- **Project Brain:** Discover project structure and conventions; store assertions, provenance, revision membership, and operational records; retrieve relevant knowledge.
- **Preflight:** Inspect remote integration baseline, local workspace, relevant branches and PRs; assess potential overlaps and dependencies; propose branch naming.
- **Context Service:** Produce compact or detailed immutable Context Packages with freshness, authority, evidence, and uncertainty.
- **Policy & Execution:** Enforce grants and tool scopes; guard writes; run checks; record progress; suspend on boundary violations.
- **Delivery Coordinator:** Prepare reviewable per-Work-Unit commit title/body and exact scope; draft PR title/body; verify actual Git/PR state.

## 5. Knowledge architecture

### 5.1 Project Brain

One local SQLite-backed brain per project. The graph represents entities and **assertions about relationships**, not unqualified permanent edges. Assertions include stable identifiers, evidence references, verification/authority metadata, and applicability to coherent source snapshots. The same entity can participate in different effective relationships across branches.

**Durable state:** tasks, clarification decisions, approval grants, execution checkpoints, unpublished findings.

**Derived state:** scanned symbols, graph edges, search indexes, detected conventions, snapshot membership.

Logical separation is mandatory; a **single SQLite database with separate tables** is the recommended MVP physical layout, not a frozen requirement. Derived indexes must be rebuildable without destroying durable state.

### 5.2 Shared knowledge vault

Git-backed, Obsidian-compatible Markdown with stable IDs independent of filenames, minimal required frontmatter (no more than four mandatory fields), typed relations and provenance. Lifecycle state is separate from authority. AI-generated inferences remain provisional until appropriately validated. Project-restricted material cannot be promoted into a more widely visible vault. Reviewed shared changes follow Git policy.

### 5.3 Project Intelligence Profile (ADR-006)

Learn project languages/versions, frameworks, manifests, build/test commands, CI, naming and architectural conventions, security restrictions, and scoped exceptions. Explicit approved standards outrank inferred patterns. Store the source and applicable revision for nontrivial findings. Do not manually duplicate obvious repository information.

### 5.4 Discovery and invalidation (ADR-007/008)

Start with light inventory (manifests, configurations, representative source/tests/docs); expand to relevant subsystems; perform deep investigation only along task-relevant dependency paths. Track depth per region/objective: D0 unknown, D1 inventory, D2 structural, D3 verified behavioral detail. Track **freshness separately from depth**.

Changes invalidate directly affected findings, trigger dependent revalidation, and notify possible downstream impact without indiscriminately discarding the whole graph. Failed refresh preserves the last valid snapshot, marked stale or incomplete as appropriate. Discovery budgets are adjustable and provisional; budget exhaustion never licenses unsupported conclusions or weaker safety checks. Use FTS5 and graph traversal before considering embeddings.

## 6. Snapshot and workspace consistency

### 6.1 Snapshot contract (ADR-003)

- Every published source-derived snapshot identifies a coherent Git revision.
- Assertions are immutable; **snapshot membership** determines applicability.
- Branch-derived knowledge is not silently mixed with integration-branch knowledge.
- Queries resolve one coherent snapshot or explicitly report inability/staleness.
- Snapshot publication is atomic; indexing failures do not corrupt the last valid snapshot.
- Dirty-worktree overlays are identified separately and never disguised as committed source.
- Snapshot retention/retirement must preserve any referenced execution evidence.

### 6.2 Workspace contract (ADR-004)

- Inspect workspace before modifying files; distinguish clean, dirty non-overlapping, and dirty overlapping conditions.
- Unrelated developer edits must be preserved; a non-overlapping dirty file does not by itself block work.
- Inspect/reconcile overlapping changes before writing; no automatic reset/stash.
- Before each write, compare current content with the version against which the edit was prepared (e.g., hash or equivalent).
- Track the agent's own expected intermediate version separately; if another actor changes the file, re-evaluate rather than overwrite.
- Never claim a clean or safe workspace based solely on an outdated initial check.

## 7. Git branch preflight (ADR-005)

**Read-only preflight precedes implementation and branch creation authorization.** Fetch/inspect the latest verified integration baseline; inspect relevant active PRs and branches for file, symbol, contract, and dependency overlap; protect local changes. Distinguish a potential conflict from a proven blocking dependency. No unauthorized rebase, force-push, or integration-branch write.

New task branches originate from the latest verified integration branch, not from another task branch by accident. Branch creation, implementation, commit, push, PR creation, and merge are separately controlled. Published branch rebases require explicit approval and repository policy compliance.

**Configurable naming:** user/project branch prefix such as `mb/`, independent naming pattern (e.g., `{prefix}{type}/{issue}-{slug}`), collision checks, Git ref validation, optional issue-less stable task IDs. Project configuration outranks user defaults; repository policy remains authoritative. Existing branches are not automatically renamed.

## 8. Task, Work Unit, and planning contracts (ADR-012)

**Work Item:** external issue/story/bug/feature or local request.

**Work Unit:** coherent, reviewable change with a proposed commit.

**Execution Step:** internal operation; not a commit boundary.

Default to one Work Unit per issue unless meaningful decomposition is justified; preserve explicit ticket subtasks unless authorized to reorganize. A bug fix and its regression test normally form one Work Unit. Work Units need not be independently executable but must have reviewable boundaries and appropriate verification.

| Mode | Planning requirement | Typical boundary |
|---|---|---|
| Quick | Objective, scope, verification | Localized fix |
| Standard | Compact approach, acceptance, dependencies | Moderate feature |
| Deep | Impact analysis, alternatives, design, checkpoints | Architectural/risky work |
| Explore | Questions, hypotheses, evidence strategy | Investigation only; no implicit code modification |

Planning depth depends on complexity and uncertainty; approval depth depends on authority, scope, risk, and consequences. Approval is event-driven, not a mandatory gate after each phase. Material ambiguity, architectural decisions, scope expansion, risk escalation, or restricted operations require appropriate human decision. Routine authorized implementation does not.

## 9. Context Package contract (ADR-009)

An immutable, revision-scoped **read-only knowledge artifact**, not an authorization token. Logical sections: `identity`, `integrity`, `project`, `knowledge`, `coordination`, `uncertainties`; sections beyond identity/integrity can be empty.

A package communicates repository revision, workspace status, coverage, freshness, project conventions, relevant assertions/contracts, active PR overlap, unresolved questions, and evidence references. **Relevance**, **authority**, and **verification** are independent dimensions. Provisional hypotheses cannot masquerade as established facts.

Retrieval priority: mandatory applicable constraints; direct task evidence; dependency/coordination context; supporting historical knowledge. Mandatory constraints cannot be silently dropped due to token budgets. Compact and detailed views share critical warnings. Expansion creates a new immutable version preserving source and visibility boundaries.

Illustrative logical operations:

```text
context.create(task_id, revision, budget)
context.expand(package_id, focus, depth)
context.inspect(package_id)
context.validate(package_id)
```

Context must be revalidated before modifying work if relevant source or coordination assumptions may have changed.

## 10. Execution contract (ADR-010)

Each modifying run requires an **Execution Envelope** bound to task, plan revision, approved scope, workspace/baseline, allowed tools/operations, constraints, budget, and verification obligations. Knowledge retrieval cannot grant execution authority. Tool enforcement must be real, not merely prompt text.

Execution states: `ready`, `running`, `verifying`, `suspended`, `completed`; completion outcome separately records `passed`, `failed`, or `incomplete`. Autonomy levels L0–L4 express delegated scope, **not** unrestricted access. L2 implementation after approval; L3 bounded independent execution; L4 longer multi-step work with checkpoints.

Permissions are granular: investigate, modify authorized files, run local checks, create branch, stage, commit, push, create PR, merge. Risk or scope escalation suspends affected work. Repeated unsuccessful attempts require **observable progress** (new evidence, narrowed cause, passing check), not model self-assessment; budgets cannot override safety. Checkpoints persist approvals, modified-file state, observations, and outstanding verification so work can resume after interruption.

Verification must be measured against approved acceptance criteria and existing behavior, not only newly written tests. Report executed commands, exit codes, revision/environment, failures, skipped checks, and limitations accurately. A test result is not valid for arbitrary later changes.

## 11. Delivery contract (ADR-011)

Every completed implementation Work Unit yields a **proposed commit** with title, body, exact files/hunks or identifiable change scope, verification evidence, and limitations. Conventional Commits is a configurable recommendation, not a universal standard.

**Default: prepare only.** No staging, committing, pushing, PR creation, or merging unless separately authorized or configured within repository policy. PR title/body are prepared from actual changes and recorded verification. Use issue-closing keywords only when the PR resolves the entire issue.

For v0.1, use **sequential commit checkpoints**: complete and verify Work Unit A, present its proposed commit, wait for developer commit (or separately authorized commit), confirm Git boundary, then begin Work Unit B. This avoids mingling uncommitted changes. More complex patch queues are deferred.

Delivery state is separate from execution: `not_ready`, `commit_proposed`, `awaiting_commit`, `committed`, `pr_proposed`, `pr_open`, `integrated`. Git/GitHub are the sources of truth for actual commit and PR status.

## 12. Example configuration (illustrative, not final schema)

```yaml
git:
  integration_branch: master  # resolved from repository policy where possible
  branches:
    prefix: "mb/"
    naming_pattern: "{prefix}{type}/{issue}-{slug}"
    create_from_integration: true
    check_remote_collision: true

brain:
  storage:
    engine: sqlite
    layout: single  # provisional physical choice
  retrieval:
    strategy: fts5_graph_first

tasks:
  planning: adaptive
  default_work_units: single

delivery:
  work_units:
    decomposition: adaptive
    preserve_ticket_subtasks: true
  commits:
    strategy: per_work_unit
    format: conventional
    prepare_title: true
    prepare_body: true
    stage: false
    execute: false
    checkpoint: sequential
  pull_requests:
    prepare_title: true
    prepare_body: true
    create: false
    merge: false
  push:
    execute: false
```

Configuration precedence: explicit authorized task override, project settings, user settings, built-in defaults, **subject always to repository/organization policy**. An override cannot grant an operation prohibited by higher authority. The exact schema, type mapping, and validation implementation remain to be specified.

## 13. Operational flow

```text
Task intake
  -> Project identification and scoped discovery
  -> Read-only Git/GitHub preflight
  -> Task classification and clarification (when material)
  -> Context Package and proportional plan
  -> Scoped authorization / Execution Envelope
  -> Work Unit implementation and evidence-backed verification
  -> Commit proposal; sequential human/authorized commit checkpoint
  -> Next Work Unit (if any)
  -> PR title/body proposal (not automatically published)
  -> On confirmed merge, reconcile integration-baseline knowledge
```

Branch creation occurs only after its separate authorization and verified integration baseline. Exploration may end with findings without any code changes or commit proposals.

## 14. Contract-level invariants and failure behavior

| Concern | Required behavior |
|---|---|
| Mixed source revisions | Never present a hybrid graph as one verified snapshot |
| Stale assertion | Label stale/revalidate; never silently elevate to current |
| Dirty unrelated file | Preserve and continue when safe |
| Dirty overlapping file | Inspect/reconcile before write |
| Concurrent modification | Detect before overwrite; suspend/replan as needed |
| Active overlapping PR | Surface evidence; distinguish potential vs blocking |
| Unauthorized scope expansion | Suspend affected work and request grant |
| Incomplete verification | Report accurately; never claim success |
| Repeated failed attempts | Require observable progress; stop at budget or safety boundary |
| Interrupted execution | Recover from durable checkpoints |
| Missing commit authorization | Prepare proposal; do not stage or commit |
| Missing PR authorization | Prepare draft; do not create or publish |
| Confidential knowledge | Enforce visibility before retrieval/promotion |
| Failed index refresh | Preserve last valid snapshot with accurate freshness status |

## 15. MVP implementation boundary and milestones

**Include:** local CLI-first application; project SQLite brain; staged discovery; revision membership; FTS5/graph retrieval; Git and `gh` adapters; scoped Context Packages; task router; approvals/envelopes; safe write checks; execution evidence; sequential commit proposals; PR drafts; durable recovery.

**Defer:** embeddings, distributed brain, full vault sync, multi-agent orchestration, automated merge/deploy, cross-repository graph federation, patch queues, real-time collaborative editing, autonomous knowledge promotion.

| Milestone | Deliverable | Exit gate |
|---|---|---|
| M0 | Contracts, configuration, task identity, adapters, schema | Persist and inspect a task safely |
| M1 | Project discovery, snapshots, provenance, retrieval | Explain relevant code with verifiable references |
| M2 | GitHub intake, preflight, context, planning | Grounded plan without modifying repository |
| M3 | Scoped execution, write protection, verification, checkpoints | Complete one authorized Work Unit safely |
| M4 | Commit proposals, sequential checkpoints, PR draft, recovery | Issue-to-PR-draft flow without unauthorized publication |
| M5 | Real-repository pilot, failure injection, simplification | Demonstrated reliability and measured usefulness |

## 16. MVP acceptance tests

1. Propose a branch using configured prefix (`mb/`), validated name, and verified integration baseline.
2. Detect and report a relevant active PR without falsely claiming all overlap blocks work.
3. Preserve dirty unrelated files; require reconciliation for overlapping modifications.
4. Reject an unauthorized file write and detect a concurrent change before overwrite.
5. Return provenance and freshness for retrieved assertions, without mixing divergent branch snapshots.
6. Rebuild derived indexes without losing durable tasks/approvals/checkpoints.
7. Classify Quick/Standard/Deep/Explore and request clarification only for material uncertainty.
8. Enforce an approval grant tied to task, plan revision, scope, and workspace.
9. Record actual verification commands/results and never fabricate a pass.
10. Recover an interrupted task from durable state.
11. Produce distinct commit title/body/scope proposals for meaningful Work Units.
12. Never stage/commit/push/create PR/merge under default configuration.
13. Prepare an accurate PR draft with issue references and explicit verification limitations.
14. Prevent project-restricted knowledge from leaking into a broader shared vault.
15. Preserve the last valid brain snapshot after failed refresh.

**Pilot reliability targets:** zero unauthorized modifications, zero lost developer changes, and 100% traceability for reported test results. Measure task time, intervention count, retrieval usefulness, and unnecessary clarifications against a real baseline; no unmeasured speedup claims.

## 17. Open implementation choices and design-freeze rules

**Open:** implementation language; one vs two physical SQLite files (single recommended); CLI/API transport; first AI adapter; exact table design; discovery thresholds; performance budgets; vault indexing internals; exact configuration schema; repository-specific integration branch and commit conventions.

**Frozen:** the approved safety, authority, provenance, planning, snapshot, workspace, Git, and delivery contracts. An architectural contract change requires an explicit amendment with rationale and impact. Internal implementation improvements that preserve contracts do not require new ADRs.

## 18. Contract artifacts and implementation status

The first skill and the following **draft contract schemas** have been authored for v0.1.0. Their structural and semantic conformance still needs automated validation and engine implementation:

| Artifact | Responsibility |
|---|---|
| `aew/skills/aew-task/SKILL.md` | Read-only task analysis and proportional planning |
| `contracts/task.schema.json` | Task identity, assessment, Work Units, planning |
| `contracts/context.schema.json` | Revision-scoped knowledge, evidence, freshness |
| `contracts/approval.schema.json` | Approval grant structure; not itself an authority token |
| `contracts/execution.schema.json` | Work Unit execution envelope and verification |
| `contracts/delivery.schema.json` | Commit proposals, PR drafts, publication observations |

JSON Schema validates structure; cross-contract references, authenticity of approvals, source consistency, and protected operations require semantic checks in the engine. In particular, no model-authored document can authorize itself.

**Not yet implemented:** executable engine, persistent Project Brain, guarded execution, GitHub integration, schema fixtures/tests, or a completed pilot. The approved contracts are design requirements, not evidence of working enforcement.

## 19. Documentation maintenance and change control

- `README.md` is the entry point for project purpose, current capability, onboarding, and roadmap.
- This file is the authoritative consolidated architecture and invariant reference.
- `contracts/*.schema.json` defines machine-readable structures; `skills/*/SKILL.md` defines agent procedures.
- Update documentation in the same Work Unit whenever behavior, contracts, configuration, or supported capabilities change.
- Keep **approved**, **proposed**, and **implemented** status distinct. Do not describe unimplemented controls as functioning safeguards.
- Contract amendments require an explicit decision and impact review; ordinary implementation refinements that preserve approved invariants do not.
- Validate examples against schemas and tests as soon as the validation harness exists.

**Next engineering artifact:** a minimal v0.1.0 read-only task fixture and schema validation test, followed by the engine adapter boundary for Git/GitHub preflight.
