# ADR-002 — Shared Knowledge Vault Structure and Governance

**Status:** Accepted
**Date:** 2026-11-22  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Shared knowledge organization, metadata, identity, provenance, visibility, promotion, and lifecycle  
**Depends on:** ADR-001 — Hybrid Knowledge Storage Strategy

---

## 1. Context

ADR-001 establishes that AEW uses two complementary knowledge domains:

- A local SQLite Project Brain for project-specific operational and derived knowledge.
- A shared Git-backed Markdown vault for reusable engineering knowledge.

The shared vault must remain human-readable, portable, and independent of any AI provider.

However, using Markdown alone does not establish a reliable knowledge system.

Without conventions, a shared vault can become an unstructured collection of documents containing duplicated information, ambiguous authority, obsolete guidance, and project-specific assumptions presented as universal rules.

AEW therefore requires a minimal governance model defining:

- How knowledge documents are identified.
- How documents are organized.
- How metadata is represented.
- How relationships between documents are maintained.
- How project knowledge is promoted.
- How knowledge is updated and deprecated.
- How provenance and authority are preserved.
- How sensitive or project-specific information is prevented from leaking into shared knowledge.
- How AI agents should interpret retrieved knowledge.

The solution must avoid turning a simple Markdown vault into an unnecessarily complex content management system.

---

## 2. Decision

AEW will use a **Git-backed, Markdown-native knowledge vault with stable document identities, lightweight structured metadata, explicit relationships, and controlled knowledge lifecycle transitions**.

The vault is a reusable knowledge resource, not a replacement for project-specific Project Brains.

### 2.1 Core principles

The vault must be:

**Human-readable**

Documents remain understandable without AEW.

**Portable**

Knowledge is stored in standard Markdown files and can be maintained using ordinary Git and Markdown tools.

**Structured but lightweight**

A small metadata convention provides identity, classification, provenance, and lifecycle information.

**Traceable**

Knowledge retains references to its sources and relevant architectural decisions.

**Authority-aware**

A document's presence in the vault does not automatically make its contents authoritative.

**Incrementally maintainable**

Documents can be added, revised, linked, deprecated, or superseded without rebuilding the entire vault.

**Project-independent by default**

Shared documents should express reusable knowledge rather than undocumented assumptions about one particular repository.

---

## 3. Vault Organization

### 3.1 Recommended directory structure

The initial vault should use a small number of broad knowledge categories.

```text
knowledge-vault/
├── README.md
├── index.md
│
├── architecture/
│   ├── patterns/
│   └── principles/
│
├── engineering/
│   ├── practices/
│   ├── testing/
│   └── debugging/
│
├── technologies/
│   ├── languages/
│   ├── frameworks/
│   ├── databases/
│   └── infrastructure/
│
├── modernization/
│   ├── strategies/
│   ├── integration/
│   └── migration/
│
├── security/
│
└── references/
```

This structure is an initial convention, not a fixed taxonomy.

Directories should be introduced when they improve navigation.

AEW must not require every knowledge category to exist before the vault becomes useful.

### 3.2 Directory responsibilities

**Architecture**

Reusable architectural patterns, principles, and tradeoffs.

**Engineering**

General development practices, testing strategies, debugging techniques, and engineering workflows.

**Technologies**

Reusable technical knowledge about languages, frameworks, databases, and infrastructure.

**Modernization**

Patterns for legacy integration, migration, interoperability, and incremental modernization.

**Security**

Reusable security engineering guidance, defensive patterns, and known classes of implementation risk.

**References**

Curated supporting material that does not fit the other categories.

### 3.3 Taxonomy independence

Knowledge identity must not depend on its directory path.

Moving a document between categories must not invalidate its stable identifier or relationships.

Directories are organizational aids, not primary keys.

---

## 4. Document Identity

Every managed knowledge document must have a stable identifier.

### 4.1 Identity format

The initial identifier format is:

`kb:<namespace>:<identifier>`

Examples:

```text
kb:architecture:hexagonal-architecture
kb:engineering:idempotent-operations
kb:modernization:anti-corruption-layer
kb:security:least-privilege
```

Identifiers must be unique within the vault.

### 4.2 Identity properties

A knowledge identifier must:

- Remain stable across file renames.
- Remain stable across directory moves.
- Be independent of the document title.
- Be unique within the vault.
- Be suitable for references from Project Brains and Context Packages.

### 4.3 Identity changes

An identifier should not be changed merely because a document is reorganized.

When a knowledge concept is substantially replaced, the preferred approach is to create a new identifier and establish an explicit supersession relationship.

### 4.4 Duplicate prevention

The vault must reject duplicate stable identifiers during validation.

Two files containing the same identifier must not be silently treated as independent knowledge records.

---

## 5. Document Metadata

Managed knowledge documents will use YAML front matter.

This is a metadata convention only; it does not require the AEW engine itself to adopt YAML for its configuration or operational contracts.

### 5.1 Required metadata

Every managed knowledge document must include:

| Field | Purpose |
|---|---|
| `id` | Stable knowledge identifier |
| `title` | Human-readable title |
| `status` | Knowledge lifecycle state |
| `kind` | Knowledge classification |
| `visibility` | Permitted sharing boundary |
| `created` | Creation date |
| `updated` | Last substantive update date |
| `sources` | Provenance references |

### 5.2 Optional metadata

Optional fields may include:

- `tags`
- `summary`
- `related`
- `supersedes`
- `superseded_by`
- `applicability`
- `reviewed_at`
- `owner`

Metadata should remain concise.

Avoid introducing fields that have no current consumer.

### 5.3 Example document

```markdown
---
id: kb:engineering:idempotent-operations
title: Idempotent Operations
status: active
kind: practice
visibility: shared
created: 2026-11-22
updated: 2026-11-22
sources:
  - type: reference
    value: internal-engineering-guidance
tags:
  - reliability
  - distributed-systems
related:
  - kb:engineering:retry-strategies
---

# Idempotent Operations

## Summary

An idempotent operation produces the same intended
persistent result when repeated with the same
logical request.

## Applicability

Useful when implementing retryable operations,
message processing, and failure recovery.

## Constraints

Idempotency must be defined relative to the
operation's observable contract.

## Implementation Considerations

Document the idempotency boundary and ensure
duplicate requests do not create duplicate
persistent effects.

## Limitations

Idempotency does not automatically guarantee
transactional consistency or exactly-once delivery.
```

The example is illustrative. It does not imply that the referenced documents or source identifiers already exist.

---

## 6. Knowledge Classification

The `kind` field identifies the primary purpose of a document.

The initial supported classifications are:

| Kind | Meaning |
|---|---|
| `principle` | General engineering principle |
| `pattern` | Reusable architectural or implementation pattern |
| `practice` | Repeatable engineering practice |
| `reference` | Curated technical reference |
| `decision` | Explicitly adopted shared engineering decision |
| `lesson` | Generalized finding from previous work |

The classification system should remain extensible through reviewed changes.

Avoid creating separate document types for minor variations in content.

### 6.1 Knowledge versus instructions

A knowledge document is reference material.

It must not be treated as an executable instruction simply because an AI agent retrieved it.

For example, a document describing a Git cleanup procedure does not authorize Codex to execute destructive Git commands.

Authorization remains governed by the active task, repository policy, and AEW execution controls.

---

## 7. Knowledge Lifecycle

Every managed document has a lifecycle status.

### 7.1 Supported states

| Status | Meaning |
|---|---|
| `draft` | Knowledge under preparation or review |
| `active` | Maintained and available for ordinary use |
| `needs_review` | Potentially stale, incomplete, or disputed |
| `deprecated` | Retained for historical context but discouraged for new use |
| `superseded` | Replaced by another knowledge document |
| `archived` | Preserved but excluded from ordinary retrieval |

### 7.2 Activation

A document becomes active only after the required review or acceptance process.

The presence of a Markdown file does not automatically establish its accuracy.

### 7.3 Review

Documents may be marked `needs_review` when:

- A supporting source changes.
- A technical assumption becomes questionable.
- A contradiction is discovered.
- A newer implementation pattern becomes relevant.
- A project investigation identifies a possible limitation.

Review requirements should be proportional to the document's impact.

### 7.4 Deprecation and supersession

Deprecated and superseded documents should remain available for historical traceability.

A superseded document should reference its replacement.

The replacement should reference the document it supersedes.

AEW should prefer active knowledge during retrieval while preserving access to historical material.

---

## 8. Knowledge Relationships

The vault must support explicit relationships between knowledge documents.

### 8.1 Initial relationship model

The initial implementation should support:

- Related knowledge.
- Supersession.
- Source provenance.
- Applicability references.

Relationships should use stable identifiers where possible.

### 8.2 Example

```yaml
related:
  - kb:engineering:retry-strategies

supersedes:
  - kb:engineering:legacy-retry-guidance
```

### 8.3 Graph integration

The Project Brain may index vault relationships for efficient retrieval.

However, the Markdown documents remain the portable representation of shared knowledge.

Derived graph indexes must be rebuildable from the vault.

### 8.4 Broken references

Validation should identify references to nonexistent knowledge identifiers.

Broken references should not be silently ignored.

The system may distinguish:

- Resolved internal references.
- Explicit external references.
- Unresolved references.

---

## 9. Provenance and Evidence

Every managed knowledge document must retain provenance.

### 9.1 Provenance requirements

Provenance should identify the origin of a claim or document.

Possible source types include:

- Official technical documentation.
- Published standards.
- Accepted architectural decisions.
- Verified repository investigations.
- Human-authored engineering guidance.
- Reviewed internal documentation.

### 9.2 Source authority

Not all sources have equal authority.

AEW must distinguish source identity from source credibility.

For example, a historical investigation may provide useful evidence without establishing a universally applicable rule.

### 9.3 Derived knowledge

Knowledge derived from a project investigation must retain a reference to the original project evidence when promoted.

If the original evidence cannot be shared, the promoted document must not imply that the evidence is publicly available.

### 9.4 Verification claims

A document must not claim verification unless an actual verification procedure or authoritative source supports the claim.

AI-generated reasoning alone is not sufficient to establish empirical verification.

---

## 10. Visibility and Sharing Boundaries

Knowledge visibility must be explicit.

### 10.1 Initial visibility categories

| Visibility | Meaning |
|---|---|
| `private` | Restricted to the owning user or designated local context |
| `team` | Approved for a defined team or organization |
| `shared` | Approved for the configured shared vault audience |

These categories are logical classifications.

Actual filesystem permissions, Git repository access, and remote hosting controls must enforce the corresponding sharing boundaries.

### 10.2 Default visibility

Newly proposed knowledge must not automatically become broadly shared.

When visibility is uncertain, use the most restrictive applicable classification until reviewed.

### 10.3 Sensitive information

Promotion must prevent accidental disclosure of:

- Credentials.
- Access tokens.
- Private keys.
- Customer data.
- Internal infrastructure details.
- Confidential repository content.
- Proprietary source code.
- Other information restricted by applicable policy.

A document's classification is not a substitute for content review.

### 10.4 Cross-project boundaries

Project-specific knowledge must not be copied into the shared vault without an explicit promotion decision.

The shared vault must not become a mechanism for bypassing project access controls.

---

## 11. Knowledge Promotion

ADR-001 establishes that knowledge promotion must be controlled.

ADR-002 defines the corresponding lifecycle.

### 11.1 Promotion workflow

```text
Project Brain
     |
     v
Candidate knowledge
     |
     v
Evidence and applicability review
     |
     v
Visibility and confidentiality review
     |
     v
Generalization and normalization
     |
     v
Explicit approval
     |
     v
Shared Markdown document
     |
     v
Vault validation
     |
     v
Git-backed publication
```

### 11.2 Promotion requirements

Before promotion:

1. Identify the source project and evidence.
2. Determine whether the knowledge is genuinely reusable.
3. Remove inappropriate project-specific assumptions.
4. Review confidentiality and visibility.
5. Assign a stable knowledge identifier.
6. Preserve provenance.
7. Obtain approval.
8. Validate metadata and references.
9. Publish through the authorized Git workflow.

### 11.3 AI-assisted promotion

An AI agent may:

- Identify candidate reusable knowledge.
- Draft a generalized explanation.
- Suggest metadata.
- Identify related documents.
- Propose source references.
- Prepare a Markdown diff.

An AI agent must not independently grant sharing authorization.

### 11.4 Promotion failure

If required evidence, visibility review, or approval is unavailable, the promotion must remain pending.

AEW must not silently publish the candidate.

---

## 12. Vault-to-Project Consumption

Shared knowledge may inform Project Brain investigations and Context Package generation.

However, shared guidance must remain distinct from repository-specific evidence.

### 12.1 Applicability

A general pattern is not automatically applicable to every project.

AEW should consider:

- Project language and framework.
- Existing architecture.
- Domain constraints.
- Repository conventions.
- Version compatibility.
- Relevant evidence.
- Known limitations.

### 12.2 Authority

Shared knowledge must not override:

- Accepted project ADRs.
- Repository security policies.
- Verified implementation evidence.
- Explicit task constraints.
- Trusted authorization decisions.

### 12.3 Context Packages

Context Packages may include references to relevant vault documents.

They must preserve:

- Document identity.
- Document revision or content digest.
- Lifecycle status.
- Provenance.
- Applicability limitations.

The package must not silently treat a mutable vault document as immutable context.

---

## 13. Git Integration

The shared vault uses Git for history and collaboration.

### 13.1 Git responsibilities

Git provides:

- Version history.
- Change review.
- Branching.
- Reversion.
- Collaboration.
- Portable distribution.

### 13.2 Publication boundaries

Creating or editing a local Markdown document does not automatically authorize:

- Git staging.
- Commit execution.
- Push.
- Pull request creation.
- Merge.

These operations remain governed by AEW authorization and repository policy.

### 13.3 Concurrent changes

Concurrent vault modifications should use normal Git review and conflict resolution.

AEW must not automatically overwrite conflicting edits.

### 13.4 History preservation

Substantive knowledge revisions should remain traceable through Git history.

Supersession is preferred over silently rewriting historical decisions.

---

## 14. Indexing and Retrieval

The vault may be indexed by AEW for faster retrieval.

### 14.1 Initial indexing

The first implementation should support:

- Stable ID lookup.
- Title lookup.
- Category filtering.
- Tag filtering.
- Relationship traversal.
- Lifecycle filtering.
- Basic text search.

### 14.2 Optional advanced retrieval

Future implementations may add:

- Full-text indexing.
- Semantic search.
- Embeddings.
- Graph-assisted ranking.
- Relevance scoring.

These are optional optimizations, not prerequisites for the initial vault.

### 14.3 Retrieval behavior

Retrieval should prioritize:

- Relevance.
- Applicability.
- Active lifecycle status.
- Source quality.
- Document freshness.
- Explicit relationships.

Retrieval results must not conceal important uncertainty.

### 14.4 Index consistency

Derived indexes must be rebuildable from the Git-backed Markdown source.

A corrupted or stale index must not silently replace source content.

---

## 15. Architectural Invariants

The following invariants become normative if ADR-002 is accepted.

### INV-001 — Markdown portability

Shared knowledge remains readable independently of AEW.

### INV-002 — Stable identity

Document identity is independent of filename, directory, and title.

### INV-003 — Explicit provenance

Managed knowledge retains identifiable source references.

### INV-004 — Explicit lifecycle

Every managed document has a defined lifecycle status.

### INV-005 — No implicit authority

Vault membership does not establish correctness, applicability, or execution authority.

### INV-006 — Controlled promotion

Project-specific knowledge cannot become shared knowledge without an explicit promotion decision.

### INV-007 — Visibility preservation

Knowledge must not cross visibility boundaries without authorization.

### INV-008 — Historical traceability

Superseded or deprecated knowledge remains traceable.

### INV-009 — Rebuildable indexes

Derived search and graph indexes can be reconstructed from Markdown source.

### INV-010 — Context integrity

Context Packages referencing vault knowledge must preserve the relevant document identity and version.

### INV-011 — Git publication separation

Preparing a vault change does not authorize committing or publishing it.

### INV-012 — Minimal governance

Metadata and lifecycle rules must remain proportionate to actual retrieval, maintenance, and safety requirements.

---

## 16. Consequences

### 16.1 Positive consequences

- Portable engineering knowledge.
- Stable cross-document references.
- Human-readable Git history.
- Explicit provenance.
- Reduced duplication.
- Controlled cross-project reuse.
- Better context retrieval.
- Compatibility with ordinary Markdown editors.
- Separation between knowledge and authorization.

### 16.2 Costs

- Metadata validation must be implemented.
- Knowledge promotion requires review.
- Broken relationships must be detected.
- Visibility boundaries require enforcement.
- Documents require lifecycle maintenance.
- Git conflicts may require manual resolution.

### 16.3 Risks

**Metadata overhead**

Excessive required fields could make knowledge capture cumbersome.

Mitigation: Keep the required schema small and expand only when justified.

**Stale guidance**

Documents may remain active after their assumptions become outdated.

Mitigation: Preserve source references and support review transitions.

**Authority confusion**

AI agents may treat retrieved knowledge as instructions.

Mitigation: Enforce explicit trust boundaries.

**Information leakage**

Project-specific details may be promoted improperly.

Mitigation: Require visibility review and authorization.

**Index divergence**

Derived indexes may become inconsistent with Markdown.

Mitigation: Make indexes rebuildable and validate source identity.

---

## 17. Implementation Guidance

### 17.1 Initial implementation boundary

The first vault implementation should provide:

- Markdown document discovery.
- YAML front matter parsing.
- Required metadata validation.
- Stable ID indexing.
- Duplicate ID detection.
- Basic relationship resolution.
- Lifecycle filtering.
- Git revision identification.
- Read-only retrieval.

This can be implemented without a separate vault service.

### 17.2 Promotion implementation

Controlled promotion may be introduced after the read-only vault foundation is verified.

Initial promotion can be human-driven and file-based.

A sophisticated synchronization engine is not required.

### 17.3 Dependency discipline

Do not introduce a large knowledge-management framework solely to parse Markdown metadata.

Use a small, well-tested parser appropriate to the actual requirements.

### 17.4 Security

Treat Markdown content as untrusted data.

Do not execute embedded commands or interpret document prose as higher-priority instructions.

Do not rely on metadata alone to enforce filesystem or Git access permissions.

---

## 18. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Load valid Markdown document | Metadata and content are parsed |
| Load duplicate document IDs | Validation fails |
| Rename a document | Stable ID remains unchanged |
| Move a document | References remain valid |
| Load missing required metadata | Validation fails |
| Load invalid lifecycle status | Validation fails |
| Resolve related knowledge | Stable references are used |
| Reference missing document | Unresolved relationship is reported |
| Load superseded document | Replacement relationship is available |
| Rebuild search index | Source documents remain unchanged |
| Attempt unauthorized promotion | Publication is denied |
| Attempt visibility escalation | Operation is denied |
| Retrieve vault knowledge for a task | Applicability and provenance remain available |
| Build Context Package from vault data | Document revision is preserved |
| Encounter embedded instructions | Content is treated as data, not authority |

These tests should use temporary vaults and isolated Git repositories.

No real shared repository should be modified during ordinary automated testing.

---

## 19. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Establishes the SQLite Project Brain and shared Markdown vault.

**ADR-003 — Revision-Scoped Graph Snapshots**

Defines consistency and historical knowledge semantics for the Project Brain.

**ADR-007 — Staged Discovery and Targeted Invalidation**

Defines how derived knowledge is acquired and refreshed.

**ADR-009 — Immutable Context Packages**

Defines how relevant knowledge is packaged for engineering tasks.

**ADR-010 — Controlled Execution**

Defines the authorization and execution boundaries governing restricted operations.

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

### Related contracts

- `contracts/context.schema.json`
- `contracts/approval.schema.json`

A dedicated vault metadata schema may be introduced when the implementation requires machine-readable validation.

---

## 20. Open Questions

The following details remain implementation choices:

1. Whether vault metadata validation should use JSON Schema, a typed model, or another lightweight mechanism.
2. Whether the initial vault is maintained in a separate Git repository or a dedicated directory within an existing repository.
3. Whether stable identifiers should use descriptive slugs, generated identifiers, or both.
4. Whether knowledge ownership should be mandatory.
5. How review scheduling should be implemented.
6. Whether a lightweight local index is sufficient or a dedicated SQLite vault index becomes useful.
7. How organization-level visibility policies integrate with local vault metadata.

These questions should be resolved incrementally rather than becoming prerequisites for basic read-only retrieval.

---

## 21. Acceptance Criteria

ADR-002 can be marked **Accepted** when the engineer confirms the following architectural choices:

- Shared knowledge remains Git-backed Markdown.
- Documents use stable identities independent of paths.
- Lightweight YAML front matter provides structured metadata.
- Knowledge has explicit lifecycle and provenance.
- Relationships use stable identifiers.
- Cross-project promotion requires explicit approval.
- Visibility boundaries are preserved.
- Derived indexes remain rebuildable.
- Vault knowledge is reference material, not executable authority.
- Git publication remains separately authorized.

---

## 22. Decision Summary

AEW's shared knowledge vault will use Git-backed Markdown with stable document identities, lightweight metadata, explicit relationships, provenance, and lifecycle governance.

The vault will support human curation and AI-assisted retrieval without becoming a centralized service or an autonomous source of authority.

Project-specific intelligence remains in the Project Brain.

Reusable engineering knowledge may be promoted into the shared vault through a controlled, traceable process.

**Knowledge should be easy to capture, easy to retrieve, easy to verify, and difficult to misrepresent as authority.**