# ADR-003 — Revision-Scoped Graph Snapshots

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Project Brain consistency, knowledge assertions, repository revisions, snapshot membership, and concurrent knowledge updates  
**Related milestones:** M2 — Project Brain Foundation; M3 — Context Packages

---

## 1. Context

The Adaptive Engineering Workbench (AEW) maintains a persistent Project Brain containing structured knowledge about a software repository.

This knowledge includes:

- Components and modules.
- Interfaces and contracts.
- Dependencies and relationships.
- Source-code observations.
- Architectural assertions.
- Evidence references.
- Repository conventions.
- Investigation results.
- Knowledge freshness and depth.

The Project Brain is intended to survive individual AI sessions and reduce repeated repository investigation.

However, source repositories are mutable.

Branches advance, files change, dependencies evolve, and multiple agents or developers may investigate different repository states concurrently.

A knowledge graph that simply updates its existing records whenever new information is discovered can produce inconsistent results.

For example, consider a repository at two revisions.

**Revision A**

```text
CustomerController
        |
        | calls
        v
CustomerService
        |
        | calls
        v
LegacyCustomerRepository
```

**Revision B**

```text
CustomerController
        |
        | calls
        v
CustomerService
        |
        | calls
        v
CustomerGateway
```

If AEW updates only part of its graph, a subsequent query might incorrectly report that `CustomerService` depends on both `LegacyCustomerRepository` and `CustomerGateway`.

That combined result may not represent either repository revision.

This is particularly dangerous when AI-assisted implementation relies on the graph to understand architectural dependencies.

The Project Brain therefore requires a consistency model that preserves coherent historical observations while supporting incremental updates.

---

## 2. Decision

AEW will use **immutable knowledge assertions organized into coherent, revision-scoped graph snapshots with explicit snapshot membership**.

A snapshot represents a logically consistent view of project knowledge associated with a defined repository revision and observation context.

New investigations do not silently overwrite previously published assertions.

Instead, they create new assertions or reuse existing immutable assertions and associate them with an appropriate snapshot.

### 2.1 Core model

The conceptual model consists of:

1. Repository revisions.
2. Knowledge entities.
3. Immutable assertions.
4. Evidence references.
5. Graph snapshots.
6. Snapshot membership.

The Project Brain must preserve the relationship between these elements.

### 2.2 Repository revision

A repository revision identifies the source-code state relevant to a snapshot.

At minimum, the model must support:

- Repository identity.
- Git commit identifier.
- Branch or reference context where relevant.
- Observation metadata.

A branch name alone is insufficient because branches are mutable references.

The Git commit identifier is the primary immutable reference to committed repository content.

### 2.3 Knowledge entity

A knowledge entity represents an identifiable concept within a project.

Examples include:

- Source file.
- Module.
- Class.
- Function.
- API endpoint.
- Database table.
- Configuration component.
- Domain concept.

Entities require stable identifiers within their defined identity scope.

Entity identity must not be confused with an assertion about the entity.

For example, the existence of `CustomerService` and the claim that it calls `CustomerGateway` are distinct pieces of information.

### 2.4 Immutable assertion

An assertion represents a specific knowledge claim.

Examples:

```text
CustomerService --calls--> CustomerGateway

CustomerGateway --implements--> CustomerPort

CustomerController --depends_on--> CustomerService
```

Once published, an assertion's meaning and provenance must not be modified in place.

A corrected or changed claim must be represented through a new assertion or a new snapshot membership decision.

### 2.5 Graph snapshot

A graph snapshot represents a coherent collection of assertions applicable to a defined repository observation.

Snapshots have stable identities.

Published snapshots are immutable.

A newer snapshot may reuse assertions from an earlier snapshot when their continued applicability has been established.

### 2.6 Explicit membership

An assertion is included in a snapshot only through an explicit membership relationship.

AEW must not determine snapshot membership merely by selecting every assertion created before a particular timestamp.

Creation time is not equivalent to revision applicability.

---

## 3. Conceptual Data Model

The following diagram describes the logical relationships.

```text
Project
   |
   +-- Repository Revision
   |       |
   |       +-- Commit ID
   |       +-- Reference Context
   |
   +-- Graph Snapshot
           |
           +-- Snapshot Identity
           +-- Repository Revision
           +-- Observation Context
           |
           +-- Membership
                  |
                  +-- Assertion A
                  |      |
                  |      +-- Subject
                  |      +-- Predicate
                  |      +-- Object
                  |      +-- Evidence
                  |
                  +-- Assertion B
                  |
                  +-- Assertion C
```

The physical database schema may differ from this conceptual representation.

The important requirement is preservation of the consistency relationships.

### 3.1 Example

Consider two snapshots:

```text
Snapshot S1
Repository commit: A

Members:
    Assertion 101
    Assertion 102
    Assertion 103
```

```text
Snapshot S2
Repository commit: B

Members:
    Assertion 101
    Assertion 104
    Assertion 105
```

Assertion 101 remains applicable and is reused.

Assertions 102 and 103 are not automatically carried forward.

Assertions 104 and 105 represent knowledge applicable to the newer revision.

The historical contents of S1 remain unchanged.

---

## 4. Snapshot Consistency

### 4.1 Coherent revision boundary

Every snapshot must identify the repository revision against which its source-derived knowledge was evaluated.

A snapshot must not silently combine assertions verified against incompatible revisions.

### 4.2 Reusing assertions

An assertion may belong to multiple snapshots.

However, reuse requires a defensible applicability determination.

Possible supporting evidence includes:

- Relevant source files are unchanged.
- The affected dependency region is unchanged.
- A targeted verification confirms continued applicability.
- The assertion describes durable project knowledge whose authority is independent of the changed source region.

The exact reuse strategy may vary by knowledge type.

### 4.3 Partial knowledge

A snapshot does not need to represent the entire repository.

It may cover only the regions investigated so far.

Coverage must be explicit.

An absent assertion must not automatically mean the corresponding relationship does not exist.

For example, if a snapshot contains no relationship between two components, AEW must distinguish:

- Relationship verified absent.
- Relationship not investigated.
- Relationship previously known but currently stale.
- Relationship outside the snapshot's coverage.

### 4.4 Unknown and provisional information

A snapshot may contain provisional assertions.

However, provisional status must remain visible.

Snapshot membership does not automatically establish that an assertion is verified.

### 4.5 Dirty workspaces

A Git commit identifies committed repository content, not necessarily the current working tree.

When an investigation includes uncommitted modifications, AEW must record an additional workspace observation identity or fingerprint.

Assertions derived from uncommitted content must not be presented as verified against the clean commit alone.

The exact workspace fingerprint representation is an implementation detail, but the distinction is mandatory.

---

## 5. Snapshot Lifecycle

Snapshots follow a controlled publication lifecycle.

### 5.1 Building

A snapshot under construction may accumulate candidate membership records and evidence.

It must not be exposed as a finalized coherent snapshot.

### 5.2 Validation

Before publication, AEW must validate:

- Repository identity.
- Revision identity.
- Membership integrity.
- Assertion references.
- Evidence references.
- Consistency of source applicability.
- Required snapshot metadata.

### 5.3 Publication

A snapshot becomes published through an atomic state transition.

Readers must not observe a partially published snapshot.

### 5.4 Historical preservation

Published snapshots remain immutable.

A later investigation must not rewrite an earlier snapshot to reflect newer repository behavior.

### 5.5 Supersession

A newer snapshot may supersede an earlier snapshot as the preferred view for a particular repository context.

Supersession does not delete the historical snapshot.

### 5.6 Garbage collection

Storage cleanup may eventually remove unreachable derived artifacts under an explicit retention policy.

However, cleanup must not invalidate retained snapshots, evidence references, or audit requirements.

Automatic historical deletion is not required for the initial implementation.

---

## 6. Concurrency Model

Multiple investigations may operate concurrently.

For example:

- Agent A investigates authentication at commit A.
- Agent B investigates persistence at commit A.
- Agent C investigates authentication at commit B.

AEW must prevent these activities from silently corrupting one another's knowledge.

### 6.1 Concurrent reads

Published snapshots may be read concurrently.

Readers should observe a stable snapshot identity and membership set.

### 6.2 Concurrent investigations

Investigations may create independent candidate assertions.

They must not mutate already published assertions.

### 6.3 Concurrent publication

Snapshot publication must be transactional.

If concurrent writers attempt to publish competing updates, the persistence layer must preserve both consistency and traceability.

A writer must not silently replace another writer's published snapshot.

### 6.4 Conflict handling

Conflicting assertions may coexist as distinct claims with different evidence, revisions, or verification states.

AEW must not automatically resolve conflicts by selecting whichever assertion was written last.

Conflict resolution requires an explicit reconciliation process.

### 6.5 Optimistic coordination

The initial implementation may use optimistic concurrency control around snapshot publication.

The exact transaction and version-checking strategy is an implementation choice.

The invariant is that conflicting writes cannot silently produce a mixed or partially published snapshot.

---

## 7. Assertion Provenance

Every assertion must retain sufficient provenance to support its interpretation.

### 7.1 Required provenance concepts

The logical model must support:

- Assertion identity.
- Source or evidence reference.
- Observation context.
- Repository revision applicability.
- Verification status.
- Relevant timestamps.

Additional metadata may include:

- Discovery method.
- Investigation depth.
- Confidence or uncertainty.
- Responsible agent or process.
- Related task.

### 7.2 Evidence types

Evidence may include:

- Source-code locations.
- Configuration files.
- Test results.
- Build outputs.
- Accepted ADRs.
- Verified documentation.
- Explicit human decisions.

Evidence must be interpreted according to its source and authority.

### 7.3 Evidence validity

An evidence reference must not imply that the evidence remains current indefinitely.

Repository changes may invalidate the applicability of source-derived evidence.

### 7.4 Historical traceability

AEW should be able to explain why an assertion appeared in a historical snapshot.

This requires preserving the relationship between assertion, evidence, and snapshot membership.

---

## 8. Knowledge Freshness and Depth

ADR-003 establishes the snapshot consistency foundation.

ADR-007 and ADR-008 further define knowledge maintenance.

### 8.1 Freshness

Freshness describes whether an assertion's evidence remains applicable to the repository state being considered.

### 8.2 Depth

Depth describes how thoroughly the relevant knowledge region has been investigated.

The approved depth model is:

- D0 — Discovery.
- D1 — Structural.
- D2 — Behavioral.
- D3 — Deep semantic analysis.

### 8.3 Independent dimensions

Freshness and depth must remain independent.

An assertion can be:

- Current and shallow.
- Current and deep.
- Stale and shallow.
- Stale and deep.

A deep historical investigation must not automatically be considered current.

### 8.4 Snapshot coverage

Snapshot metadata should make it possible to determine which regions and depths are represented.

AEW must not claim complete repository understanding when only partial discovery has occurred.

---

## 9. Context Package Integration

ADR-009 defines immutable Context Packages.

Those packages must reference coherent Project Brain snapshots.

### 9.1 Snapshot binding

A Context Package must identify the snapshot from which its knowledge was selected.

### 9.2 Revision binding

The package must identify the relevant repository revision and workspace context.

### 9.3 Integrity

Package integrity must be verifiable independently of mutable Project Brain state.

### 9.4 Expansion

When additional knowledge is required, AEW may create a new Context Package.

The new package must preserve revision consistency.

If the repository changes, AEW must explicitly determine whether a new snapshot or revalidation is required.

### 9.5 No implicit mixing

A Context Package must not silently combine assertions from snapshots associated with incompatible repository observations.

Cross-revision comparisons are permitted when explicitly represented as comparisons rather than a single current-state view.

---

## 10. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Immutable assertions

Published assertions cannot be modified in place.

### INV-002 — Immutable published snapshots

Published snapshot identity, revision binding, and membership cannot change.

### INV-003 — Explicit membership

Snapshot membership must be represented explicitly.

### INV-004 — Revision coherence

A snapshot must not silently combine incompatible source-code revisions.

### INV-005 — Historical reproducibility

Previously published snapshots must remain reconstructable under the applicable retention policy.

### INV-006 — Evidence traceability

Assertions must retain identifiable provenance.

### INV-007 — No implicit verification

Snapshot membership does not automatically make an assertion verified.

### INV-008 — Partial coverage honesty

Missing knowledge must not be represented as verified absence.

### INV-009 — Transactional publication

Readers must never observe partially published snapshots.

### INV-010 — Concurrency safety

Concurrent investigations must not silently overwrite published knowledge.

### INV-011 — Workspace distinction

Knowledge derived from uncommitted changes must be distinguishable from knowledge derived from committed repository content.

### INV-012 — Context consistency

Context Packages must bind to coherent snapshots and preserve their revision applicability.

---

## 11. Alternatives Considered

The following alternatives summarize the architectural tradeoffs relevant to the accepted decision.

They are not intended as a verbatim record of every original design discussion.

### 11.1 Mutable graph with in-place updates

**Advantages**

- Simpler initial data model.
- Lower apparent storage overhead.
- Easy retrieval of the latest known state.

**Disadvantages**

- Historical knowledge is overwritten.
- Concurrent investigations can interfere.
- Mixed-revision relationships are difficult to detect.
- Context reproducibility becomes unreliable.

**Disposition:** Rejected as the primary consistency model.

### 11.2 Full graph copy for every revision

**Advantages**

- Straightforward snapshot interpretation.
- Strong isolation between revisions.

**Disadvantages**

- Potentially excessive duplication.
- Higher storage and update costs.
- Inefficient for repositories with small incremental changes.

**Disposition:** Not required. Immutable assertions may be reused through explicit membership.

### 11.3 Timestamp-based assertion selection

**Advantages**

- Simple query model.
- Minimal snapshot metadata.

**Disadvantages**

- Time does not establish repository applicability.
- Concurrent investigations may produce misleading ordering.
- Historical reconstruction can combine incompatible observations.

**Disposition:** Rejected as a substitute for explicit snapshot membership.

### 11.4 Rebuild the entire knowledge graph after every change

**Advantages**

- Simpler conceptual freshness model.
- Avoids some incremental invalidation complexity.

**Disadvantages**

- Unnecessary repeated analysis.
- Poor scalability for large repositories.
- Increased AI and compute costs.
- Slower engineering workflows.

**Disposition:** Not selected. AEW uses targeted invalidation and staged discovery.

---

## 12. Consequences

### 12.1 Positive consequences

- Reproducible historical knowledge.
- Stronger revision consistency.
- Safer concurrent investigations.
- Reliable Context Package provenance.
- Incremental graph maintenance.
- Explicit uncertainty.
- Better debugging of knowledge inconsistencies.
- Reduced risk of stale architectural assumptions.

### 12.2 Costs

- Additional persistence relationships.
- Snapshot publication logic.
- Revision applicability checks.
- Knowledge reconciliation procedures.
- More sophisticated invalidation tracking.
- Potential storage growth.

### 12.3 Risks

**Incorrect assertion reuse**

An assertion may be carried into a new snapshot despite a relevant behavioral change.

Mitigation: Require evidence-based applicability checks.

**Snapshot proliferation**

Frequent investigations may produce many snapshots.

Mitigation: Use appropriate retention and compaction strategies without compromising historical guarantees.

**Incomplete evidence**

An assertion may lack sufficient evidence to establish current applicability.

Mitigation: Preserve provisional or unknown status.

**Concurrent publication conflicts**

Multiple writers may attempt incompatible updates.

Mitigation: Transactional publication and explicit conflict handling.

---

## 13. Implementation Guidance

### 13.1 Persistence technology

ADR-001 establishes SQLite as the initial Project Brain persistence technology.

ADR-003 does not require a dedicated graph database.

### 13.2 Suggested logical tables

The initial schema may include:

```text
projects
repository_revisions
knowledge_entities
knowledge_assertions
evidence
graph_snapshots
snapshot_memberships
knowledge_regions
```

These names are illustrative, not mandatory physical table names.

### 13.3 Assertion identity

Assertions require stable identifiers.

The implementation must distinguish:

- Entity identity.
- Assertion identity.
- Snapshot identity.
- Evidence identity.

Do not use a mutable file path as the sole identity of an architectural concept.

### 13.4 Snapshot membership

A membership record should associate:

- Snapshot identifier.
- Assertion identifier.
- Applicability or membership metadata where necessary.

Membership must not be inferred solely from assertion creation timestamps.

### 13.5 Transaction boundaries

Publishing a snapshot must be atomic.

A transaction should ensure that required membership records and metadata are valid before publication becomes visible.

### 13.6 Derived indexes

Search and graph traversal indexes may be regenerated.

Regenerating an index must not modify the meaning of published assertions or snapshots.

### 13.7 Initial implementation scope

Milestone M2 should begin with:

- Immutable assertions.
- Evidence references.
- Revision identities.
- Snapshot creation.
- Explicit membership.
- Transactional publication.
- Historical retrieval.

Advanced reconciliation and storage optimization may follow after the core invariants are verified.

---

## 14. Verification

The following tests must demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Publish snapshot S1 | Membership becomes stable and queryable |
| Create snapshot S2 | S1 remains unchanged |
| Reuse an assertion in S2 | Same immutable assertion may belong to both snapshots |
| Attempt to modify published assertion | Operation is rejected |
| Attempt to modify published membership | Operation is rejected |
| Query historical snapshot | Original assertion set is returned |
| Publish incomplete snapshot transaction | No partial snapshot becomes visible |
| Concurrent publication | No silent overwrite or mixed membership |
| Query uncovered knowledge region | Result indicates unknown or uncovered |
| Investigate dirty workspace | Workspace observation identity is preserved |
| Create Context Package | Snapshot and revision identities are retained |
| Attempt incompatible revision mixing | Operation is rejected or explicitly represented as comparison |
| Rebuild derived index | Published knowledge remains unchanged |

Tests should use isolated SQLite databases and disposable repository fixtures.

Verification must rely on observed behavior, not assumed correctness.

---

## 15. Related Decisions and Contracts

### Related ADRs

- **ADR-001 — Hybrid Knowledge Storage Strategy:** Establishes SQLite-backed Project Brains.
- **ADR-002 — Shared Knowledge Vault Structure and Governance:** Defines reusable knowledge and its authority boundaries.
- **ADR-006 — Project Intelligence Profile:** Defines repository-specific discovery.
- **ADR-007 — Staged Discovery and Targeted Invalidation:** Defines incremental knowledge maintenance.
- **ADR-008 — Progressive Knowledge Depth:** Defines investigation depth independently of freshness.
- **ADR-009 — Immutable Context Packages:** Defines bounded task context derived from coherent snapshots.

### Related contracts

- `contracts/context.schema.json`
- `contracts/task.schema.json`

Additional internal Project Brain persistence contracts may be introduced during M2.

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 16. Open Implementation Questions

The accepted architecture does not yet prescribe:

1. The exact SQLite table definitions and indexes.
2. The algorithm for determining assertion applicability across revisions.
3. The mechanism for computing workspace fingerprints.
4. Snapshot retention and compaction policies.
5. Whether snapshots use explicit complete membership sets or an internal delta representation with equivalent semantics.
6. The precise concurrency-control strategy for publication.
7. The policy for promoting provisional assertions to verified status.
8. The indexing strategy for efficient graph traversal.

These decisions should be made during implementation when supported by concrete requirements.

They must preserve the architectural invariants established above.

---

## 17. Acceptance and Compliance

ADR-003 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Published assertions are immutable.
- Published snapshots are immutable.
- Snapshot membership is explicit and coherent.
- Repository revisions remain identifiable.
- Historical knowledge can be reconstructed.
- Concurrent investigations cannot silently corrupt published state.
- Context Packages preserve snapshot identity.
- Missing or stale knowledge is not misrepresented as verified current knowledge.

Compliance requires implementation and test evidence.

The existence of this document does not establish that these capabilities have been implemented.

---

## 18. Decision Summary

AEW's Project Brain uses immutable knowledge assertions organized into coherent, revision-scoped graph snapshots.

Each snapshot explicitly identifies its assertion membership and repository observation context.

New investigations create new assertions or snapshots rather than rewriting historical knowledge.

Assertions may be reused across snapshots when their applicability is supported by evidence.

This model provides the consistency foundation for incremental discovery, knowledge freshness, concurrent investigations, and immutable Context Packages.

**The Project Brain must preserve not only what AEW knows, but also when, where, and why that knowledge was considered applicable.**