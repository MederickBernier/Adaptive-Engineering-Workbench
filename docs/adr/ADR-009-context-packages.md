# ADR-009 — Immutable Context Packages

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Task context assembly, immutable knowledge packages, identity, integrity, provenance, revision consistency, authority, uncertainty, and context expansion  
**Related milestones:** M3 — Immutable Context Packages; M4 — Adaptive Planning; M5 — Authorization and Controlled Execution

---

## 1. Context

The Adaptive Engineering Workbench (AEW) maintains a persistent Project Brain containing evidence-backed knowledge about software repositories.

This knowledge includes architectural components, dependencies, conventions, assertions, verification guidance, and historical investigations.

However, the Project Brain may contain considerably more information than an individual engineering task requires.

Providing the entire knowledge base to an AI agent would introduce several problems:

- Excessive context consumption.
- Reduced relevance.
- Increased reasoning overhead.
- Greater exposure to stale information.
- Difficulty distinguishing verified facts from assumptions.
- Difficulty reproducing decisions made during earlier sessions.
- Potential mixing of incompatible repository revisions.

A second problem arises during long-running tasks.

The repository may change after an agent begins investigating a problem.

The Project Brain may acquire new assertions.

Other agents may publish new snapshots.

If the active task context changes implicitly, AEW may no longer be able to establish which information supported a particular decision.

For example:

```text
T0 — Task begins at commit A.

T1 — Context is assembled from snapshot S1.

T2 — Agent produces an implementation plan.

T3 — Repository advances to commit B.

T4 — Project Brain publishes snapshot S2.

T5 — Agent resumes implementation.
```

If the agent silently consumes knowledge from S2 while continuing to rely on the original plan, it may combine assumptions from incompatible repository states.

AEW therefore requires a bounded, immutable, revision-consistent representation of task context.

---

## 2. Decision

AEW will use **immutable Context Packages** to deliver task-relevant Project Brain knowledge to AI-assisted engineering workflows.

A Context Package is a versioned, integrity-verifiable artifact containing a coherent selection of knowledge associated with an explicit repository and Project Brain observation.

Each package must identify:

1. Its stable package identity.
2. Its content integrity.
3. Its repository identity.
4. Its repository revision.
5. Its Project Brain snapshot.
6. Its workspace observation.
7. Its knowledge coverage.
8. Its freshness and investigation depth.
9. Its included assertions and evidence.
10. Its provenance and authority boundaries.
11. Its coordination information.
12. Its known limitations and uncertainties.

A published Context Package must never be modified in place.

When additional context is required, AEW creates a new package with a new identity.

### 2.1 Core distinction

The Project Brain is a persistent knowledge system.

A Context Package is an immutable selection of knowledge for a particular engineering context.

The package does not replace the Project Brain.

It establishes a reproducible knowledge boundary for planning, execution, and verification.

### 2.2 Context Packages are not authorization

A Context Package may contain repository policies, architectural constraints, and references to approval requirements.

However, the package does not independently authorize restricted operations.

Authorization remains governed by the Approval Contract and deterministic execution policy.

---

## 3. Context Package Identity

Every Context Package must have a stable, unique identity.

### 3.1 Package identifier

The package identifier distinguishes one published package from every other package.

It must not be reused for different content.

### 3.2 Identity scope

The package identity must be associated with:

- Project.
- Repository.
- Task or investigation context.
- Repository observation.
- Project Brain snapshot.

### 3.3 Identity immutability

Once published, the package identifier must refer to exactly one immutable package representation.

Changing the package contents requires creating a new package.

### 3.4 Package relationships

Packages may reference other packages through explicit relationships such as:

- Derived from.
- Expands.
- Replaces for current task use.
- Revalidated from.

These relationships do not permit mutation of an earlier package.

### 3.5 No implicit latest-package substitution

An execution bound to package P1 must not silently begin using package P2 merely because P2 is newer.

A package change requires an explicit execution-context transition and applicable revalidation.

---

## 4. Repository Revision Binding

A Context Package must identify the repository state represented by its knowledge.

### 4.1 Committed revision

The package must record the relevant Git commit identifier.

A branch name alone is insufficient because branches can advance.

### 4.2 Branch context

The package may record the branch or reference associated with the observation.

This provides useful context but does not replace the immutable commit identity.

### 4.3 Project Brain snapshot

The package must reference a coherent Project Brain snapshot as defined by ADR-003.

### 4.4 Workspace fingerprint

When uncommitted changes are relevant, the package must identify the corresponding workspace observation or fingerprint.

The package must not present knowledge derived from uncommitted changes as if it came solely from the clean committed revision.

### 4.5 Revision consistency

Assertions included as current-state knowledge must be applicable to the package's repository observation.

### 4.6 Historical knowledge

Historical assertions may be included when relevant.

However, they must be explicitly identified as historical and must not be presented as current repository facts.

### 4.7 Cross-revision comparisons

A package may contain explicitly labeled comparisons between revisions.

For example, a migration task may require comparing commit A with commit B.

Such comparisons must preserve the separate revision identities.

They must not be represented as one undifferentiated current-state graph.

---

## 5. Package Integrity

A Context Package must support deterministic integrity verification.

### 5.1 Integrity requirements

The package must include or reference:

- An integrity algorithm.
- A content digest.
- A defined canonical representation.
- The package identity.

### 5.2 Canonicalization

Integrity verification requires a deterministic representation of package content.

The implementation must define how equivalent serialized content is canonicalized.

For example, object key ordering and whitespace must not cause accidental integrity ambiguity.

### 5.3 Digest scope

The digest must cover all fields whose modification would alter the package's meaning, authority classification, evidence, or revision binding.

The digest field itself must be excluded from its own digest calculation using a precisely defined rule.

### 5.4 Verification

Consumers must be able to verify package integrity before relying on the package.

### 5.5 Tampering

A package whose content does not match its declared digest must be rejected.

### 5.6 Integrity versus authenticity

A content digest establishes consistency between bytes and a declared digest.

It does not independently prove who created the package or whether its contents are trustworthy.

Package provenance and trusted issuance must remain separate concerns.

### 5.7 Storage independence

Integrity verification must not require access to mutable Project Brain state.

A retained package should remain verifiable independently of later knowledge updates.

---

## 6. Package Contents

A Context Package contains a bounded selection of information relevant to an engineering task.

### 6.1 Identity and integrity

Required concepts include:

- Package ID.
- Schema version.
- Repository identity.
- Task context.
- Repository revision.
- Snapshot identity.
- Workspace observation.
- Integrity metadata.

### 6.2 Project intelligence

Relevant project characteristics may include:

- Languages.
- Frameworks.
- Build systems.
- Test tooling.
- Repository conventions.
- Architectural characteristics.

These originate from the Project Intelligence Profile defined by ADR-006.

### 6.3 Knowledge components

Relevant components may include:

- Modules.
- Classes.
- Functions.
- Interfaces.
- Services.
- Database structures.
- Configuration boundaries.

### 6.4 Knowledge assertions

Assertions must retain:

- Stable identity.
- Subject and relationship.
- Object or value.
- Evidence references.
- Verification status.
- Revision applicability.
- Relevant uncertainty.

### 6.5 Architectural contracts

The package may include relevant:

- API contracts.
- Domain invariants.
- Accepted ADRs.
- Interface definitions.
- Compatibility constraints.

### 6.6 Verification guidance

The package may include:

- Relevant test commands.
- Build commands.
- Test locations.
- Known verification limitations.

Discovered verification commands must not be represented as successfully executed checks.

### 6.7 Coordination information

The package may include relevant:

- Active pull requests.
- Branch dependencies.
- Concurrent work.
- Known integration risks.

Coordination observations must retain their source and observation context.

### 6.8 Uncertainties

The package must explicitly represent unresolved questions relevant to the task.

Unknown information must not be silently replaced with assumptions.

---

## 7. Knowledge Coverage

A Context Package must communicate what has and has not been investigated.

### 7.1 Coverage scope

Coverage may identify:

- Included repository regions.
- Investigated components.
- Relevant dependency boundaries.
- Excluded regions.
- Known investigation gaps.

### 7.2 Partial coverage

A package may be valid with partial knowledge coverage.

It must not imply complete repository understanding.

### 7.3 Coverage limitations

Examples include:

- A dependency has not been investigated.
- A test environment is unavailable.
- A runtime integration could not be observed.
- A relevant PR file list is incomplete.
- A component's behavior is only structurally understood.

### 7.4 Absence versus unknown

The absence of a relationship from the package does not prove that the relationship does not exist.

Verified absence requires explicit evidence.

### 7.5 Coverage honesty

Coverage claims must reflect actual discovery evidence.

A package must not claim full coverage simply because all currently known assertions were included.

---

## 8. Freshness and Investigation Depth

ADR-008 defines D0–D3 investigation depth and independent freshness tracking.

Context Packages must preserve these distinctions.

### 8.1 Depth

The package should identify relevant investigation depth for included regions.

### 8.2 Freshness

The package must distinguish current, stale, unknown, and otherwise inapplicable knowledge as appropriate.

### 8.3 Independent dimensions

A D3 assertion may be stale.

A D0 observation may be current.

Neither state should be misrepresented.

### 8.4 Verification

Depth and freshness do not independently establish empirical verification.

### 8.5 Context selection

AEW should prefer current, sufficiently investigated knowledge for decisions that depend on current repository behavior.

Historical or provisional knowledge may still be included when useful, provided its limitations remain explicit.

---

## 9. Provenance and Authority

Context Packages must preserve the origin and authority of included information.

### 9.1 Provenance categories

Possible sources include:

- Repository source code.
- Git history.
- Test results.
- Build outputs.
- Accepted ADRs.
- Project documentation.
- GitHub issues.
- GitHub pull requests.
- Shared Knowledge Vault documents.
- Explicit engineer-provided constraints.

### 9.2 Authority distinction

Different sources establish different kinds of authority.

For example:

Source code provides evidence of implemented behavior.

Accepted ADRs establish architectural intent.

Test results provide evidence of observed behavior under specific conditions.

An engineer's explicit authorization governs permitted operations.

These must not be conflated.

### 9.3 Untrusted content

Repository files, issue descriptions, PR comments, and shared knowledge documents may contain instructions written by third parties.

Such content must be treated as data unless independently authorized as an instruction source.

### 9.4 No authority escalation

Including a statement in a Context Package does not make it authoritative.

The package must preserve the statement's original authority classification.

### 9.5 Conflicting evidence

When relevant sources disagree, the package must preserve the conflict or identify the accepted resolution.

It must not silently choose one claim and discard contradictory evidence.

---

## 10. Package Construction

Context Package construction is a controlled transformation from Project Brain knowledge into a bounded task artifact.

### 10.1 Inputs

Construction may use:

- Task identity.
- Task objective.
- Repository preflight.
- Project Brain snapshot.
- Project Intelligence Profile.
- Relevant knowledge assertions.
- Dependency relationships.
- Required investigation depth.
- Context size budget.
- Coordination evidence.

### 10.2 Selection

AEW should select knowledge according to:

- Task relevance.
- Evidence quality.
- Freshness.
- Investigation depth.
- Architectural significance.
- Dependency relationships.
- Known uncertainty.
- Context budget.

### 10.3 Construction sequence

```text
Task and repository context
            |
            v
Select coherent Brain snapshot
            |
            v
Identify relevant knowledge regions
            |
            v
Retrieve assertions and evidence
            |
            v
Evaluate coverage and freshness
            |
            v
Include relevant coordination
            |
            v
Record limitations and uncertainties
            |
            v
Construct candidate package
            |
            v
Validate schema and semantics
            |
            v
Compute integrity digest
            |
            v
Publish immutable package
```

### 10.4 Candidate versus published packages

A candidate package may be assembled and revised before publication.

A published package is immutable.

### 10.5 Atomic publication

A package must not become available as a published artifact before its required validation and integrity metadata are complete.

### 10.6 Failure handling

If construction fails, AEW must not publish a partially valid package as complete.

Previously published packages remain unchanged.

---

## 11. Context Expansion

Engineering tasks may require additional investigation after an initial Context Package has been created.

AEW must support expansion without mutating existing packages.

### 11.1 Expansion model

Given package P1, AEW may create package P2 containing additional knowledge.

P2 receives a new identity and integrity digest.

### 11.2 Same-revision expansion

If the repository observation remains compatible, P2 may expand knowledge from the same snapshot or from a coherent successor snapshot whose applicability has been established.

The package must explicitly identify its actual source snapshot.

### 11.3 Changed-revision expansion

If the repository changes materially, AEW must determine whether a new Project Brain snapshot and revalidation are required.

New knowledge must not be silently inserted into P1.

### 11.4 Expansion relationships

P2 may record that it expands P1.

This relationship must not imply that every assertion in P1 remains applicable without revalidation.

### 11.5 Execution rebinding

An execution bound to P1 cannot silently adopt P2.

The execution controller must explicitly validate the context transition against the task, plan, authorization, and workspace state.

### 11.6 Historical reproducibility

P1 must remain available for reconstructing earlier planning or execution decisions.

---

## 12. Context Package Lifecycle

The logical lifecycle includes:

### 12.1 Candidate

The package is under construction.

Its contents may change.

### 12.2 Validated

The package satisfies required structural and semantic checks.

Its integrity representation is finalized.

### 12.3 Published

The package is immutable and available for consumption.

### 12.4 Referenced

A task, plan, or execution may reference the published package.

Referencing does not change its contents.

### 12.5 Superseded for task use

A newer package may become preferred for a task.

The earlier package remains historically valid as an artifact.

### 12.6 Retained or archived

Packages may be retained according to project policy.

Retention must preserve the evidence needed for required audit and reproducibility guarantees.

These lifecycle concepts do not require a separate status field in every serialized package.

The storage and registry model may manage publication state externally.

---

## 13. Task and Planning Integration

ADR-012 defines adaptive planning.

Context Packages provide the bounded knowledge used during task assessment and planning.

### 13.1 Planning input

A plan should identify the Context Package supporting its relevant assumptions.

### 13.2 Risk and uncertainty

The package's coverage, freshness, and unresolved questions inform planning complexity.

### 13.3 Work Unit construction

Relevant dependencies and architectural constraints may inform Work Unit boundaries.

### 13.4 Plan revisions

A material context change may require reassessment of the plan.

A plan must not silently continue relying on assumptions invalidated by a newer repository observation.

### 13.5 Planning proportionality

A Quick task may require a small Context Package.

A Deep task may require broader dependency and invariant coverage.

Package size should reflect relevance and risk rather than a universal minimum.

---

## 14. Execution Integration

ADR-010 defines controlled execution.

An Execution Envelope must bind to an explicit Context Package.

### 14.1 Required binding

Execution must identify:

- Package ID.
- Project Brain snapshot ID.
- Relevant repository revision.
- Workspace observation.

### 14.2 Pre-execution validation

Before execution, AEW must verify:

- Package integrity.
- Package identity.
- Repository consistency.
- Snapshot consistency.
- Relevant workspace applicability.
- Plan and authorization compatibility.

### 14.3 Context mismatch

If the execution environment no longer matches the package's assumptions, AEW must suspend or require reconciliation.

### 14.4 No implicit refresh

Execution must not silently substitute a newer Context Package.

### 14.5 Checkpointing

Durable checkpoints must retain the Context Package identity used by the execution.

### 14.6 Resumption

Resuming execution requires revalidating the package against the current repository and workspace context.

A retained package does not automatically remain applicable indefinitely.

---

## 15. Coordination Information

Context Packages may include information about active repository coordination.

### 15.1 Relevant PRs

The package may reference active pull requests affecting the task.

### 15.2 Branch dependencies

The package may identify known branch relationships or integration dependencies.

### 15.3 Observation freshness

Remote coordination information may change independently of the local repository.

The package must preserve when and how the information was observed.

### 15.4 Incomplete coordination

If PR enumeration or changed-file retrieval was incomplete, the package must preserve that limitation.

### 15.5 No permanent clearance

A Context Package containing a successful preflight observation does not provide permanent clearance for later implementation or publication.

Relevant checks must be revalidated when required.

---

## 16. Context Size and Relevance

AEW should avoid overwhelming AI agents with irrelevant information.

### 16.1 Bounded context

Context Packages should be sized according to task needs and available context budgets.

### 16.2 Relevance ranking

Selection may prioritize:

- Directly affected components.
- Relevant dependencies.
- Applicable contracts.
- Important invariants.
- Verification guidance.
- Known uncertainties.

### 16.3 Compression

AEW may provide compact summaries of supporting knowledge.

However, compression must not erase material uncertainty, authority distinctions, or revision identity.

### 16.4 Evidence references

Large evidence artifacts may be referenced rather than embedded.

References must remain resolvable under the package's retention and reproducibility requirements.

### 16.5 No silent omission of critical constraints

Context size limits must not silently remove safety-critical or architecturally binding information needed for the task.

If the required context cannot fit, AEW must report the limitation and use an explicit expansion or retrieval strategy.

---

## 17. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Immutable publication

Published Context Packages cannot be modified in place.

### INV-002 — Stable identity

A package identifier must refer to one immutable published representation.

### INV-003 — Verifiable integrity

Package content integrity must be independently verifiable.

### INV-004 — Revision binding

Packages must identify their repository revision and Project Brain snapshot.

### INV-005 — Workspace distinction

Relevant uncommitted changes must be represented through an explicit workspace observation.

### INV-006 — Coherent knowledge

Current-state assertions must be applicable to the package's repository observation.

### INV-007 — Explicit coverage

Packages must communicate knowledge coverage and limitations.

### INV-008 — Independent freshness and depth

Freshness and investigation depth must remain distinguishable.

### INV-009 — Evidence traceability

Included assertions must retain identifiable provenance.

### INV-010 — Authority preservation

Packaging knowledge must not elevate its original authority.

### INV-011 — Explicit uncertainty

Relevant unresolved questions must remain visible.

### INV-012 — Immutable expansion

Context expansion creates a new package rather than modifying an existing one.

### INV-013 — No implicit execution rebinding

An execution cannot silently substitute a different Context Package.

### INV-014 — Integrity is not authenticity

A matching digest does not independently establish trusted issuance or authorization.

### INV-015 — Coordination honesty

Incomplete or stale coordination observations must not be represented as complete current evidence.

### INV-016 — No implicit authorization

Context Packages cannot authorize restricted operations.

---

## 18. Alternatives Considered

The following alternatives summarize the tradeoffs relevant to the accepted architecture.

### 18.1 Direct mutable Project Brain queries

**Advantages**

- Simple integration.
- Always accesses the latest available knowledge.
- No package publication overhead.

**Disadvantages**

- Context can change during execution.
- Decisions become difficult to reproduce.
- Revision mixing becomes more likely.
- Checkpoint consistency is weakened.

**Disposition:** Rejected as the sole task-context mechanism.

### 18.2 Full Project Brain export per task

**Advantages**

- Broad knowledge availability.
- Simple selection logic.

**Disadvantages**

- Excessive context size.
- High retrieval overhead.
- Increased irrelevant information.
- Greater exposure to stale or unrelated knowledge.

**Disposition:** Rejected as the default approach.

### 18.3 Mutable Context Packages

**Advantages**

- Easy incremental enrichment.
- Fewer package identifiers.

**Disadvantages**

- Historical context becomes unstable.
- Integrity verification becomes ambiguous.
- Execution assumptions can change silently.
- Checkpoint reproducibility is weakened.

**Disposition:** Rejected.

### 18.4 Timestamp-only context identity

**Advantages**

- Simple metadata.
- Easy ordering.

**Disadvantages**

- Time does not establish repository revision.
- Concurrent investigations may overlap.
- Historical reconstruction remains ambiguous.

**Disposition:** Rejected as a substitute for explicit revision and snapshot identity.

### 18.5 Content hash without provenance

**Advantages**

- Simple integrity verification.
- Efficient duplicate detection.

**Disadvantages**

- Does not establish source authority.
- Does not explain why assertions are applicable.
- Cannot independently establish trusted issuance.

**Disposition:** Insufficient as the complete model.

---

## 19. Consequences

### 19.1 Positive consequences

- Reproducible engineering context.
- Stronger long-running task consistency.
- Better checkpoint recovery.
- Clear knowledge provenance.
- Reduced context bloat.
- Explicit uncertainty.
- Better revision safety.
- Traceable planning assumptions.
- Safer multi-agent coordination.
- Improved auditability.

### 19.2 Costs

- Package construction and validation.
- Integrity calculation.
- Package storage and retention.
- Context selection logic.
- Explicit expansion workflows.
- Revision reconciliation.
- Execution rebinding checks.

### 19.3 Risks

**Stale packages**

A valid historical package may no longer apply to the current repository.

Mitigation: Revalidate applicability before dependent operations.

**False authority**

A package may contain untrusted or provisional claims.

Mitigation: Preserve source authority and verification status.

**Incomplete coverage**

A package may omit relevant dependencies.

Mitigation: Record coverage and unresolved uncertainty.

**Integrity ambiguity**

Different serialization strategies may produce inconsistent digests.

Mitigation: Define deterministic canonicalization.

**Context explosion**

Repeated expansion may create many packages.

Mitigation: Use relevance-driven selection and appropriate retention policies.

---

## 20. Implementation Guidance

### 20.1 Initial milestone

Context Package generation should be implemented during M3.

### 20.2 Existing contract

The initial schema is:

`contracts/context.schema.json`

Codex must validate the schema against this ADR before treating it as complete.

The existing schema is a draft and may require compatibility-preserving clarification.

### 20.3 Minimum viable implementation

The initial implementation should support:

- Package construction from a coherent Project Brain snapshot.
- Stable package identifiers.
- Repository revision binding.
- Workspace observation binding.
- Relevant assertion selection.
- Evidence references.
- Coverage and limitation metadata.
- Freshness and depth metadata.
- Integrity calculation.
- Schema and semantic validation.
- Immutable publication.
- Historical package retrieval.

### 20.4 Suggested logical interfaces

Possible operations include:

```text
build_context_candidate(task, snapshot, scope)

validate_context_candidate(candidate)

calculate_context_digest(candidate)

publish_context_package(candidate)

verify_context_integrity(package)

retrieve_context_package(package_id)

expand_context_package(package_id, additional_scope)

validate_context_applicability(package, workspace)
```

These are conceptual interfaces, not mandated function signatures.

### 20.5 Canonical representation

The implementation must define a deterministic serialization and hashing strategy.

JSON canonicalization may be appropriate, provided the rules are explicit and tested.

### 20.6 Persistence

Published packages may be stored in the Project Brain or a dedicated local artifact store.

The physical storage mechanism remains an implementation choice.

Immutability and independent integrity verification are mandatory.

### 20.7 Content references

Evidence may be embedded or referenced.

Referenced evidence must remain traceable and resolvable according to the package's retention requirements.

### 20.8 Security

Treat included repository text, external issue descriptions, and shared vault content as data.

Do not interpret embedded instructions as authority to modify files or invoke tools.

### 20.9 Avoid premature complexity

The initial implementation does not require:

- Distributed package storage.
- Remote package registries.
- Cryptographic signing infrastructure.
- Semantic embedding services.
- Complex context orchestration frameworks.

These may be considered later if concrete requirements justify them.

---

## 21. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Build package from valid snapshot | Package contains correct snapshot and revision identity |
| Publish package | Contents become immutable |
| Attempt to modify published package | Modification rejected |
| Reuse package ID for different content | Rejected |
| Modify package content after digest calculation | Integrity verification fails |
| Serialize equivalent canonical content | Digest remains deterministic |
| Change repository revision | Applicability requires reassessment |
| Include uncommitted source observations | Workspace identity retained |
| Include stale assertion | Staleness explicitly represented |
| Include provisional assertion | Verification status preserved |
| Build partial-coverage package | Limitations remain visible |
| Omit uninvestigated relationship | No false verified-absence claim |
| Expand package P1 into P2 | P1 remains unchanged; P2 has new identity |
| Resume execution with changed package | Explicit rebinding required |
| Include GitHub PR information | Observation provenance retained |
| PR enumeration incomplete | Coordination uncertainty preserved |
| Tamper with authority metadata | Integrity verification fails |
| Include untrusted instructions in evidence | Content remains data, not authority |
| Retrieve historical package | Original content and digest remain verifiable |
| Use package without approval grant | Restricted operations remain unauthorized |

Tests should use isolated Project Brain databases and disposable repository fixtures.

Verification must rely on observed behavior.

---

## 22. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Establishes the Project Brain persistence foundation.

**ADR-002 — Shared Knowledge Vault Structure and Governance**

Defines reusable knowledge and its authority boundaries.

**ADR-003 — Revision-Scoped Graph Snapshots**

Defines coherent, immutable knowledge snapshots.

**ADR-004 — Workspace Consistency**

Defines workspace observation and concurrent modification requirements.

**ADR-005 — Git Preflight**

Provides repository and coordination evidence.

**ADR-006 — Per-Project Intelligence Profiles**

Provides project-specific technical characteristics.

**ADR-007 — Staged Discovery and Targeted Invalidation**

Defines incremental knowledge acquisition.

**ADR-008 — Progressive Knowledge Depth**

Defines depth, freshness, and coverage distinctions.

**ADR-010 — Controlled Execution**

Binds execution to explicit context identity and authorization.

**ADR-012 — Adaptive Planning**

Uses Context Packages as evidence for proportional planning.

### Related contracts

- `contracts/context.schema.json`
- `contracts/task.schema.json`
- `contracts/approval.schema.json`
- `contracts/execution.schema.json`

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 23. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact package identifier format.
2. The canonical JSON representation and digest algorithm.
3. The package storage layout.
4. The mechanism for retaining referenced evidence.
5. The context relevance-ranking algorithm.
6. The context size budgeting strategy.
7. The package expansion relationship schema.
8. The policy for revalidating stale packages.
9. The exact authority classification representation.
10. The retention policy for superseded packages.
11. The strategy for handling multi-revision comparison packages.
12. The mechanism for detecting package duplication.

These choices should be resolved during implementation using concrete requirements and verification evidence.

They must preserve the architectural invariants established above.

---

## 24. Acceptance and Compliance

ADR-009 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Published packages are immutable.
- Package identities cannot be reused for different content.
- Integrity verification is deterministic.
- Repository revision and Project Brain snapshot identity are explicit.
- Relevant workspace observations are preserved.
- Included assertions retain provenance and authority.
- Freshness, depth, coverage, and uncertainty remain distinguishable.
- Context expansion creates a new package.
- Execution cannot silently switch packages.
- Context Packages do not grant execution authorization.

Compliance requires observed verification evidence.

The existence of this ADR does not establish that these capabilities have been implemented.

---

## 25. Decision Summary

AEW uses immutable Context Packages to provide bounded, evidence-backed, revision-consistent knowledge to engineering tasks.

Each package identifies its repository observation, Project Brain snapshot, knowledge coverage, provenance, authority, and uncertainties.

Published packages have stable identities and verifiable integrity.

Additional investigation creates new packages rather than modifying existing ones.

Planning and execution must explicitly bind to the package they use.

**A Context Package is a reproducible engineering knowledge boundary, not a mutable summary and not an authorization token.**