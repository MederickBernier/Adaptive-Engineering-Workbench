# ADR-001 — Hybrid Knowledge Storage Strategy

**Status:** Accepted
**Original proposal:** 2026-11-21  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Knowledge persistence, project isolation, shared knowledge, and storage boundaries

---

## 1. Context

The Adaptive Engineering Workbench (AEW) requires persistent knowledge to support engineering work across multiple repositories, AI sessions, and development tasks.

Without persistent knowledge, AI-assisted development repeatedly rediscovers the same architectural information, dependencies, conventions, and previous decisions.

However, not all knowledge has the same characteristics.

Some information is project-specific, revision-dependent, and frequently regenerated from source code.

Other information represents durable engineering knowledge that should remain understandable and reusable independently of AEW.

A single undifferentiated storage mechanism would make it difficult to satisfy both requirements.

AEW therefore needs a storage architecture supporting:

- Persistent knowledge across sessions.
- Isolation between projects.
- Efficient graph-oriented retrieval.
- Revision-aware repository intelligence.
- Human-readable, portable knowledge.
- Explicit provenance and authority.
- Separation of durable and derived state.
- Incremental knowledge maintenance.
- Local-first operation.
- Independence from any specific AI provider.

The architecture must remain practical for individual engineers and small teams without requiring substantial infrastructure.

---

## 2. Decision

AEW will use a **hybrid knowledge storage architecture** consisting of two complementary storage domains.

### 2.1 Project Brain — SQLite

Each project maintains an isolated, local SQLite-backed Project Brain.

The Project Brain stores project-specific operational and derived knowledge.

It supports:

- Structured entities.
- Knowledge assertions.
- Graph relationships.
- Evidence references.
- Repository revision metadata.
- Knowledge snapshots.
- Discovery metadata.
- Freshness information.
- Investigation depth.
- Task and execution state.
- Local retrieval indexes.

SQLite provides transactional persistence, structured querying, and efficient retrieval without requiring a dedicated database service.

Each Project Brain belongs to a specific project context.

Knowledge from one project must not automatically become authoritative in another.

### 2.2 Shared Knowledge Vault — Git-backed Markdown

AEW will maintain a shared, human-readable knowledge vault using Markdown files.

The vault must be compatible with ordinary Markdown tooling, including Obsidian-style workflows.

Git provides version history and portability.

The vault is intended for reusable engineering knowledge such as:

- Architectural patterns.
- General engineering practices.
- Reusable technical explanations.
- Documented conventions.
- Approved knowledge abstractions.
- Cross-project lessons.
- Human-curated reference material.

The vault must remain useful without AEW.

Its contents must not depend on a proprietary database format or a particular AI provider.

### 2.3 Authoritative sources

AEW must distinguish knowledge storage from the systems that establish source truth.

For example:

- Repository source code is authoritative for observed implementation.
- Git establishes repository history and revisions.
- GitHub provides remote issue and pull request information.
- Accepted ADRs establish approved architectural decisions.
- Trusted human approval establishes authorization.

The Project Brain and shared vault preserve, index, and contextualize knowledge.

They must not silently replace authoritative sources.

### 2.4 Cross-project knowledge promotion

Project-specific knowledge may be proposed for promotion into the shared vault.

Promotion requires an explicit authorization or approval mechanism appropriate to the knowledge's authority and visibility.

Derived observations must not automatically become universal engineering rules.

Promoted knowledge must preserve relevant provenance.

---

## 3. Rationale

### 3.1 Why SQLite?

SQLite provides a useful combination of:

- Local persistence.
- Transactional consistency.
- Relational constraints.
- Structured queries.
- Indexing.
- Mature tooling.
- Minimal operational dependencies.

It is suitable for storing graph relationships through structured tables without requiring a separate graph database server.

It also supports AEW's local-first design.

### 3.2 Why Markdown?

Markdown provides:

- Human readability.
- Easy editing.
- Git-friendly diffs.
- Portability.
- Long-term accessibility.
- Compatibility with existing documentation workflows.

Shared engineering knowledge should not become inaccessible simply because AEW is unavailable.

### 3.3 Why separate project and shared knowledge?

Project intelligence and reusable engineering knowledge have different lifecycles.

Project intelligence can change whenever source code changes.

Shared engineering knowledge may remain valid across multiple projects and repository revisions.

Separating these domains reduces accidental cross-project contamination and allows independent maintenance.

### 3.4 Why a hybrid approach?

SQLite and Markdown solve different problems.

SQLite is optimized for structured operational queries and consistency.

Markdown is optimized for human interpretation, curation, and portability.

Using both avoids forcing either storage format into responsibilities for which it is poorly suited.

---

## 4. Alternatives Considered

The original proposal identified the hybrid approach as preferable to coupling all knowledge to one database or AI provider. The following alternatives summarize the relevant architectural tradeoffs; they are not presented as a verbatim record of every original discussion.

### 4.1 Markdown-only storage

**Advantages**

- Simple and portable.
- Human-readable.
- Easy Git integration.

**Limitations**

- Difficult transactional updates across multiple related records.
- Less suitable for efficient graph traversal.
- More complex revision-scoped snapshot management.
- Requires additional indexing for targeted retrieval.

**Disposition:** Not selected as the sole storage mechanism.

### 4.2 SQLite-only storage

**Advantages**

- Unified transactional storage.
- Structured querying.
- Straightforward indexing.

**Limitations**

- Shared knowledge becomes less convenient to edit manually.
- Human-readable version history is harder to maintain.
- Reusable knowledge becomes coupled to database-specific tooling.

**Disposition:** Not selected as the sole knowledge format.

### 4.3 Dedicated graph database

**Advantages**

- Native graph query capabilities.
- Rich relationship traversal.

**Limitations**

- Additional infrastructure.
- Greater operational complexity.
- Unnecessary dependency for the initial scale.
- Increased deployment and maintenance burden.

**Disposition:** Not required for the initial architecture.

### 4.4 AI-provider-managed memory

**Advantages**

- Convenient integration with a specific provider.
- Potentially reduced local implementation effort.

**Limitations**

- Provider dependency.
- Reduced portability.
- Limited control over persistence semantics.
- Difficulty enforcing revision-scoped knowledge guarantees.

**Disposition:** Not selected as AEW's authoritative persistence layer.

---

## 5. Architectural Invariants

The following invariants are mandatory if this ADR is accepted.

### INV-001 — Project isolation

Each project must have a distinct logical Project Brain.

Project-specific assertions must not be silently shared with unrelated projects.

### INV-002 — Local-first persistence

Core project knowledge must remain accessible locally without a mandatory centralized service.

### INV-003 — Knowledge provenance

Stored knowledge must retain sufficient provenance to identify its source, authority, and relevant revision or observation context.

### INV-004 — Durable and derived separation

Durable operational state and derived knowledge must be logically distinguishable.

Derived indexes must be rebuildable without destroying durable state.

### INV-005 — Shared knowledge portability

The shared knowledge vault must remain readable and usable as ordinary Markdown independently of AEW.

### INV-006 — Controlled knowledge promotion

Project-specific knowledge must not automatically become authoritative shared knowledge.

Promotion requires an explicit, traceable decision.

### INV-007 — No implicit authority escalation

Storage location does not establish authority.

An assertion copied into the Project Brain or vault does not automatically become verified, current, or approved.

### INV-008 — Revision-aware derived knowledge

Derived project knowledge must support revision applicability as defined by ADR-003.

### INV-009 — Transactional consistency

Operations that publish a coherent set of Project Brain state changes must preserve transactional consistency.

### INV-010 — Implementation independence

The architecture must not require a specific AI provider or hosted knowledge service.

---

## 6. Storage Model

### 6.1 Logical structure

```text
AEW
 |
 +-- Shared Knowledge Vault
 |    |
 |    +-- Git-backed Markdown
 |    +-- Human-curated knowledge
 |    +-- Reusable engineering patterns
 |    +-- Approved cross-project knowledge
 |
 +-- Project A
 |    |
 |    +-- Project Brain (SQLite)
 |         +-- Durable operational state
 |         +-- Derived knowledge
 |         +-- Graph assertions
 |         +-- Evidence
 |         +-- Revision snapshots
 |         +-- Retrieval indexes
 |
 +-- Project B
      |
      +-- Project Brain (SQLite)
           +-- Independent project knowledge
           +-- Independent snapshots
           +-- Independent operational state
```

### 6.2 Durable state

Examples include:

- Tasks.
- Clarification decisions.
- Approval records.
- Execution checkpoints.
- Unpublished findings.
- Persistent project configuration metadata.

Durable state must not be destroyed when derived knowledge is refreshed.

### 6.3 Derived state

Examples include:

- Discovered symbols.
- Dependency relationships.
- Graph edges derived from source code.
- Search indexes.
- Detected project conventions.
- Snapshot membership.
- Repository analysis results.

Derived state must remain associated with its evidence and revision applicability.

### 6.4 Physical SQLite layout

The recommended MVP implementation is **one SQLite database per project**, with logically separated tables for durable and derived information.

However, the decision between one physical database and multiple physical databases was not frozen in the original design.

The implementation may choose either arrangement if it preserves:

- Project isolation.
- Transactional consistency.
- Durable/derived separation.
- Snapshot coherence.
- Safe recovery.
- Rebuildability of derived indexes.

Any later physical separation must preserve these guarantees.

---

## 7. Knowledge Synchronization and Promotion

The Project Brain and shared vault must not be treated as interchangeable replicas.

Their contents serve different purposes.

### 7.1 Project-to-vault promotion

A promotion workflow should:

1. Identify candidate reusable knowledge.
2. Evaluate its evidence and applicability.
3. Remove inappropriate project-specific assumptions.
4. Obtain required approval.
5. Produce a human-readable Markdown representation.
6. Preserve source provenance.
7. Record the promotion decision.

### 7.2 Vault-to-project consumption

Shared knowledge may inform a project investigation.

However, general guidance from the vault must not override verified repository evidence.

When shared guidance conflicts with observed project behavior, AEW must preserve the distinction and report the conflict.

### 7.3 Synchronization policy

Detailed synchronization, conflict handling, and visibility rules remain implementation concerns requiring explicit design.

No automatic bidirectional synchronization is implied by this ADR.

---

## 8. Consequences

### 8.1 Positive consequences

- No mandatory database server.
- Project-specific knowledge isolation.
- Efficient structured retrieval.
- Human-readable shared knowledge.
- Git-based history for curated knowledge.
- Reduced dependency on AI vendors.
- Incremental adoption.
- Support for revision-aware Project Brain snapshots.

### 8.2 Costs

- Two storage formats must be maintained.
- Knowledge promotion requires explicit policy.
- Provenance must survive representation changes.
- The engine must manage schema migrations.
- Shared knowledge and project intelligence require distinct authority rules.

### 8.3 Risks

- Accidental promotion of provisional knowledge.
- Stale derived knowledge being treated as current.
- Loss of provenance during export.
- Conflicting edits to shared Markdown.
- Derived-index rebuilds affecting durable state.

These risks must be addressed through contracts, validation, and controlled state transitions.

---

## 9. Implementation Guidance

### 9.1 Initial implementation

Milestone M2 should establish:

- Project Brain initialization.
- SQLite schema migrations.
- Durable and derived logical partitions.
- Stable knowledge identifiers.
- Evidence references.
- Revision metadata.
- Basic graph assertions.
- Snapshot persistence.
- Targeted retrieval.
- Derived-index rebuild procedures.

### 9.2 Shared vault

The shared vault should initially use ordinary Markdown files under Git version control.

A complex synchronization engine is not required for the first vertical slice.

The initial implementation may begin with explicit import/export or promotion workflows.

### 9.3 Repository identity

Project Brain identity must be stable enough to avoid accidental reuse across unrelated repositories.

The exact identity and relocation strategy should be defined before implementing persistent project discovery.

### 9.4 Security

The engine must not treat imported Markdown or database content as trusted instructions.

Stored content is evidence or reference material unless independently established as authoritative.

Knowledge storage must not bypass the authorization system.

---

## 10. Verification

Compliance should be demonstrated through automated tests and controlled integration scenarios.

| Test | Expected result |
|---|---|
| Initialize two independent projects | Each receives isolated knowledge state |
| Restart AEW | Durable state remains available |
| Rebuild derived indexes | Durable records remain unchanged |
| Query historical knowledge | Revision applicability is preserved |
| Import shared Markdown | Source provenance remains identifiable |
| Promote project knowledge without approval | Promotion is rejected |
| Read vault without AEW | Markdown remains usable |
| Attempt cross-project assertion leakage | Isolation prevents unintended access |
| Simulate failed SQLite transaction | No partially committed logical update |
| Load provisional knowledge | Authority remains provisional |

Verification must use observed evidence rather than inferred success.

---

## 11. Related Decisions and Contracts

### Related ADRs

- **ADR-002:** Shared knowledge vault conventions — original decision details pending confirmation.
- **ADR-003:** Revision-scoped graph snapshots.
- **ADR-006:** Project intelligence profiles.
- **ADR-007:** Staged discovery and targeted invalidation.
- **ADR-008:** Progressive knowledge depth.
- **ADR-009:** Immutable Context Packages.

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `AGENTS.md`

### Related contracts

- `contracts/context.schema.json`
- `contracts/task.schema.json`

Dedicated Project Brain persistence schemas and internal APIs remain to be defined during M2.

---

## 12. Open Questions

The following implementation details are not frozen by this decision:

1. Whether durable and derived state should use one or multiple physical SQLite files.
2. The precise SQLite table layout and migration strategy.
3. Shared vault directory and metadata conventions.
4. Cross-project promotion approval mechanics.
5. Project identity and repository relocation handling.
6. Vault conflict reconciliation.
7. Optional encryption and backup policies.

These questions should be resolved when required by implementation, without unnecessarily expanding the architectural scope.

---

## 13. Acceptance Criteria

ADR-001 may be marked **Accepted** when the engineer confirms that:

- SQLite-backed Project Brains are the intended local persistence mechanism.
- Project knowledge remains logically isolated.
- Shared reusable knowledge uses Git-backed Markdown.
- Durable and derived state remain distinguishable.
- Knowledge provenance and revision applicability are preserved.
- Cross-project knowledge promotion requires explicit authorization.
- The physical SQLite layout remains an implementation choice.

Until that confirmation, this document remains **Proposed**.

---

## 14. Decision Summary

AEW adopts a hybrid knowledge storage strategy combining local SQLite-backed Project Brains with a shared Git-backed Markdown knowledge vault.

SQLite provides transactional, revision-aware project intelligence.

Markdown provides portable, human-readable, reusable engineering knowledge.

The two storage domains have different responsibilities and authority boundaries.

**The Project Brain preserves project understanding. The shared vault preserves reusable engineering knowledge. Neither replaces the authoritative sources from which that knowledge originates.**