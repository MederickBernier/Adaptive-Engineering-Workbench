# ADR-007 — Staged Discovery and Targeted Knowledge Invalidation

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Repository discovery, incremental analysis, knowledge reuse, dependency-aware investigation, change detection, and targeted invalidation  
**Related milestones:** M2 — Project Brain Foundation; M3 — Context Packages; M4 — Adaptive Planning

---

## 1. Context

The Adaptive Engineering Workbench (AEW) maintains a persistent Project Brain containing evidence-backed knowledge about software repositories.

This knowledge supports repository investigation, context selection, planning, implementation guidance, and verification.

However, repositories vary considerably in size and complexity.

A small application may contain a few dozen source files.

A large monorepo may contain thousands of modules, multiple applications, generated code, infrastructure definitions, and numerous dependency relationships.

Legacy modernization projects may combine languages and technologies whose dependencies cannot be discovered through conventional import analysis alone.

Performing complete repository analysis before every task would create substantial overhead.

It would also conflict with AEW's goal of making small engineering tasks faster rather than burdening them with excessive preparation.

At the same time, blindly reusing previously discovered knowledge can be unsafe when the repository has changed.

AEW therefore needs a discovery strategy that balances:

- Investigation cost.
- Task relevance.
- Knowledge freshness.
- Dependency coverage.
- Evidence quality.
- Architectural risk.
- Incremental maintenance.
- Historical reproducibility.

The system must avoid two extremes:

1. Rebuilding the entire Project Brain whenever source code changes.
2. Reusing stale knowledge without checking whether its supporting evidence remains applicable.

---

## 2. Decision

AEW will use **staged, task-driven repository discovery with targeted invalidation of affected knowledge regions**.

Discovery proceeds incrementally according to task relevance, uncertainty, risk, and existing knowledge coverage.

Previously discovered assertions may be reused when their applicability remains supported by evidence.

Repository changes must trigger analysis of potentially affected knowledge rather than indiscriminately invalidating the entire Project Brain.

### 2.1 Core principles

Discovery must be:

**Incremental**

AEW should acquire knowledge progressively instead of requiring exhaustive initial indexing.

**Task-driven**

Investigation should prioritize components relevant to the current engineering objective.

**Evidence-backed**

Discovered assertions must retain provenance.

**Revision-aware**

Knowledge must remain associated with the repository observation against which it was established.

**Dependency-aware**

Discovery and invalidation should consider relationships between components.

**Conservative**

Uncertain applicability must not be represented as verified freshness.

**Reusable**

Knowledge that remains applicable should not be rediscovered unnecessarily.

### 2.2 Architectural boundaries

ADR-007 defines how knowledge is discovered and maintained.

ADR-003 defines how knowledge is stored in coherent, immutable snapshots.

ADR-006 defines the Project Intelligence Profile.

ADR-008 defines investigation depth.

ADR-009 defines how relevant knowledge is packaged for a task.

These responsibilities must remain distinct.

---

## 3. Staged Discovery Model

AEW will use a progressive discovery process.

The stages describe investigation scope and purpose, not mandatory heavyweight workflow phases.

### 3.1 Stage S0 — Repository Orientation

**Purpose:** Establish enough repository context to navigate safely.

Typical observations include:

- Repository identity.
- Current revision.
- Top-level directory structure.
- Major languages.
- Build manifests.
- Test configuration.
- CI configuration.
- Existing architecture documentation.
- Known application boundaries.

S0 should be relatively inexpensive.

It must not require detailed analysis of every source file.

**Output:** An initial repository map and partial Project Intelligence Profile.

### 3.2 Stage S1 — Task-Relevant Discovery

**Purpose:** Identify the repository regions directly relevant to the current task.

Possible inputs include:

- Task description.
- GitHub issue.
- Known file paths.
- Component names.
- Error messages.
- Stack traces.
- Relevant tests.
- Existing Project Brain relationships.

AEW should identify candidate components and supporting evidence.

For example:

```text
Task:
    Fix null customer responses.

Candidate regions:
    CustomerController
    CustomerService
    CustomerMapper
    CustomerRepository
    CustomerMapperTest
```

S1 should avoid investigating unrelated repository regions without a concrete reason.

**Output:** A bounded set of relevant knowledge regions and initial uncertainties.

### 3.3 Stage S2 — Dependency Expansion

**Purpose:** Investigate relationships necessary to understand the task safely.

AEW may expand discovery through:

- Call relationships.
- Imports.
- Interface implementations.
- Data flow.
- Configuration dependencies.
- Shared contracts.
- Database relationships.
- Test dependencies.
- Build dependencies.
- Runtime integration boundaries.

Expansion should be guided by relevance and risk.

It must not automatically traverse every reachable dependency.

**Output:** An expanded, evidence-backed understanding of the affected engineering region.

### 3.4 Stage S3 — Focused Deep Investigation

**Purpose:** Resolve uncertainties requiring detailed analysis.

Examples include:

- Concurrency behavior.
- Transaction boundaries.
- Security-sensitive control flow.
- Domain invariants.
- Error propagation.
- State transitions.
- Legacy integration behavior.
- Complex data transformations.
- Backward compatibility constraints.

S3 is performed when justified by task complexity or unresolved risk.

It is not required for every task.

**Output:** Focused behavioral or invariant-level findings with explicit evidence and limitations.

### 3.5 Stage selection

Discovery stages are adaptive.

A Quick task may require only S0 and a small S1 investigation.

A Standard task may require S1 and targeted S2 expansion.

A Deep task may require S3 analysis of selected regions.

An Explore task may use several stages without authorizing implementation.

The system must not confuse discovery stage with knowledge depth.

Discovery stage describes the scope and purpose of investigation.

ADR-008 depth describes the level of understanding achieved for a knowledge region.

---

## 4. Knowledge Region Model

Targeted discovery requires a way to identify relevant portions of the Project Brain.

### 4.1 Knowledge region

A knowledge region represents a bounded area of project understanding.

It may correspond to:

- A source file.
- A module.
- A package.
- A service.
- An API contract.
- A database integration.
- A build subsystem.
- A domain capability.
- A group of related components.

Regions need not map one-to-one to filesystem directories.

### 4.2 Stable identity

Regions should have stable identifiers within the project.

A directory rename must not automatically imply that every conceptual component has become a different entity.

### 4.3 Region relationships

Regions may be connected through relationships such as:

- Depends on.
- Calls.
- Implements.
- Produces.
- Consumes.
- Configures.
- Tests.
- Deploys.
- Shares contract with.

Relationships must retain evidence and revision applicability.

### 4.4 Overlapping regions

Knowledge regions may overlap.

For example, an authentication component may belong to both an API subsystem and a security-sensitive domain boundary.

The model must not assume that regions form a strict directory tree.

### 4.5 Partial coverage

A region may be only partially investigated.

AEW must distinguish:

- Known entities.
- Known relationships.
- Uninvestigated relationships.
- Provisional assertions.
- Stale assertions.
- Verified absence, where established.

An incomplete region must not be treated as fully understood.

---

## 5. Discovery Inputs

AEW should prioritize existing evidence before performing new analysis.

### 5.1 Repository evidence

Examples include:

- Source code.
- Configuration.
- Dependency manifests.
- Tests.
- Build scripts.
- CI workflows.
- Documentation.
- Git history.

### 5.2 Existing Project Brain knowledge

The Project Brain may provide:

- Previously identified components.
- Dependency relationships.
- Known conventions.
- Historical investigations.
- Evidence references.
- Relevant snapshots.
- Knowledge freshness.
- Investigation depth.

### 5.3 Task evidence

Examples include:

- Issue descriptions.
- Acceptance criteria.
- Error messages.
- Logs.
- Stack traces.
- User-provided reproduction steps.
- Explicit file references.

### 5.4 External coordination

Relevant active pull requests may indicate concurrent changes or architectural dependencies.

ADR-005 governs preflight and remote coordination.

### 5.5 Shared Knowledge Vault

The shared vault may provide reusable engineering guidance.

However, shared knowledge must not replace project-specific repository evidence.

ADR-002 governs the vault's authority and provenance boundaries.

---

## 6. Discovery Planning

Before expanding investigation, AEW should determine what information is actually needed.

### 6.1 Discovery questions

A discovery plan may ask:

- Which components are directly affected?
- Which contracts might change?
- Which dependencies could influence behavior?
- Which tests establish expected behavior?
- Which assertions are already available?
- Which assertions remain current?
- Which uncertainties materially affect implementation?
- What additional investigation would reduce risk?

### 6.2 Investigation priority

Candidate regions should be prioritized according to:

- Direct task relevance.
- Dependency proximity.
- Architectural importance.
- Risk.
- Uncertainty.
- Existing coverage.
- Knowledge freshness.
- Investigation cost.

The exact ranking algorithm is an implementation choice.

### 6.3 Stopping criteria

Discovery should stop expanding when sufficient evidence exists to support the next authorized engineering decision.

Possible stopping conditions include:

- Acceptance criteria can be mapped to affected components.
- Relevant contracts are understood.
- Required verification is identified.
- Material uncertainties are resolved or explicitly reported.
- Additional investigation offers little expected value.
- The configured investigation budget is exhausted.

Budget exhaustion must preserve unresolved uncertainty.

### 6.4 No mandatory exhaustive traversal

AEW must not require every dependency reachable from a task component to be investigated.

The appropriate boundary depends on risk, evidence, and task requirements.

---

## 7. Change Detection

Targeted invalidation begins with detecting changes that may affect existing knowledge.

### 7.1 Committed changes

AEW should compare relevant repository revisions to identify:

- Added files.
- Modified files.
- Deleted files.
- Renamed files.
- Changed configuration.
- Changed dependency manifests.
- Changed interfaces.
- Changed tests.

### 7.2 Uncommitted changes

AEW must distinguish working-tree changes from committed repository history.

Assertions derived from uncommitted content require an appropriate workspace observation identity.

### 7.3 Change evidence

Change observations should retain:

- Repository identity.
- Previous revision.
- Target revision.
- Relevant changed paths.
- Change classification.
- Observation provenance.

### 7.4 Renames

A rename must not automatically be treated as deletion of one conceptual component and creation of another.

AEW may preserve entity identity when supported by evidence.

However, identity continuity must not be assumed solely because Git reports a rename.

### 7.5 Generated artifacts

Changes to generated files may require investigation of their generating source.

AEW should distinguish generated artifacts from authoritative generation inputs when the relationship is known.

---

## 8. Targeted Knowledge Invalidation

AEW must invalidate knowledge according to the evidence potentially affected by repository changes.

### 8.1 Core rule

**A repository change invalidates the applicability of affected assertions, not the historical assertions themselves.**

Published assertions and snapshots remain immutable under ADR-003.

Invalidation influences whether an assertion may be reused in a newer snapshot.

### 8.2 Direct invalidation

An assertion may require revalidation when its direct supporting evidence changes.

For example:

```text
Assertion:
    CustomerService calls CustomerRepository.

Evidence:
    src/customer/CustomerService.java

Change:
    CustomerService.java modified.

Result:
    Assertion requires applicability reassessment.
```

### 8.3 Dependency-aware invalidation

A change may affect assertions whose direct source files did not change.

For example:

```text
Changed:
    CustomerPort interface

Potentially affected:
    CustomerGateway implementation
    CustomerService dependency
    CustomerServiceTest assumptions
```

AEW should consider relevant dependency relationships when determining the invalidation frontier.

### 8.4 Conservative invalidation

When the system cannot establish whether an assertion remains applicable, it must not classify the assertion as verified current.

The assertion may remain available as historical or provisional context.

### 8.5 Targeted reuse

Assertions whose applicability is supported may be reused in a new snapshot.

For example, a frontend styling change does not necessarily invalidate a verified database schema relationship.

### 8.6 No historical mutation

Invalidation must not rewrite an earlier published snapshot.

A new snapshot should represent the newer repository observation and its current membership.

### 8.7 Explicit coverage

A new snapshot must indicate which regions were revalidated, reused, newly discovered, or left unresolved.

---

## 9. Invalidation Frontier

The invalidation frontier defines the set of knowledge regions that may be affected by a change.

### 9.1 Initial frontier

The initial frontier includes regions directly associated with changed evidence.

### 9.2 Expansion

The frontier may expand through relevant relationships.

Examples include:

- Interface consumers.
- Implementations.
- Callers.
- Shared configuration.
- Data contracts.
- Test dependencies.
- Generated artifacts.

### 9.3 Relationship direction

Invalidation must consider relationship semantics.

A change to a private implementation detail may not require the same propagation as a change to a public interface.

The system must not treat all graph edges as equivalent.

### 9.4 Unknown dependencies

Incomplete dependency coverage must remain visible.

AEW must not claim that the frontier is complete when relevant relationships have not been investigated.

### 9.5 Bounded expansion

Invalidation should remain bounded where evidence permits.

If the frontier becomes too uncertain or extensive, AEW may escalate to broader discovery.

It must not silently mark unrelated regions stale merely because broad invalidation is easier to implement.

### 9.6 Risk-sensitive behavior

Security-sensitive or contract-breaking changes may justify broader invalidation than localized implementation changes.

The scope should remain evidence-driven.

---

## 10. Snapshot Integration

ADR-003 defines immutable, revision-scoped graph snapshots.

ADR-007 defines how AEW determines which assertions are candidates for membership in a new snapshot.

### 10.1 Snapshot transition

A new repository observation may trigger:

1. Identification of changed evidence.
2. Determination of directly affected regions.
3. Dependency-aware frontier expansion.
4. Applicability assessment of existing assertions.
5. Targeted rediscovery.
6. Creation of new assertions where necessary.
7. Construction of new snapshot membership.
8. Validation and atomic publication.

### 10.2 Assertion reuse

An existing assertion may be reused when evidence supports its continued applicability.

Reuse does not modify the assertion.

### 10.3 New assertions

New findings are represented as new immutable assertions.

### 10.4 Removed applicability

An assertion that no longer applies is omitted from the new snapshot's current membership.

It remains available through historical snapshots.

### 10.5 Partial snapshot coverage

A new snapshot may have incomplete coverage.

AEW must not infer that omitted relationships are absent unless absence was explicitly verified.

---

## 11. Project Intelligence Profile Integration

ADR-006 establishes the Project Intelligence Profile.

Staged discovery maintains that profile incrementally.

### 11.1 Initial profile

S0 may identify:

- Languages.
- Frameworks.
- Build systems.
- Test tooling.
- Repository structure.

### 11.2 Targeted profile expansion

S1 and S2 may add:

- Regional conventions.
- Component boundaries.
- Dependency relationships.
- Relevant architectural characteristics.

### 11.3 Deep findings

S3 may add:

- Behavioral constraints.
- Domain invariants.
- Security-sensitive relationships.
- Failure semantics.

### 11.4 Profile invalidation

Changes to dependency manifests, build configuration, or framework-specific files may invalidate relevant profile assertions.

Unrelated profile dimensions should remain reusable when supported.

---

## 12. Progressive Knowledge Depth Integration

ADR-008 defines knowledge depth D0 through D3.

Discovery stage and knowledge depth must remain separate.

### 12.1 Discovery stage

Describes why and how far AEW expands investigation.

### 12.2 Knowledge depth

Describes the level of understanding established for a region.

### 12.3 Example

A task may begin with S1 discovery of an authentication component at D0.

S2 may establish structural relationships at D1.

S3 may investigate token lifecycle behavior at D2 or D3.

The resulting knowledge depth must reflect actual evidence, not merely the discovery stage reached.

### 12.4 Independent freshness

A region investigated to D3 at an earlier revision may become stale.

A newly inspected region may be current but only D0.

---

## 13. Context Package Integration

ADR-009 defines immutable Context Packages.

Staged discovery supplies relevant knowledge for those packages.

### 13.1 Context selection

AEW should prioritize assertions relevant to the task and its dependency frontier.

### 13.2 Coverage

Context Packages must identify the coverage achieved by discovery.

### 13.3 Uncertainty

Unresolved discovery questions must remain visible.

### 13.4 Revision consistency

A Context Package must reference a coherent Project Brain snapshot.

### 13.5 Context expansion

If additional discovery is required, AEW may create an expanded Context Package.

The original package remains immutable.

Expansion must preserve revision compatibility or explicitly establish a new context revision.

---

## 14. Adaptive Planning Integration

ADR-012 defines Quick, Standard, Deep, and Explore planning profiles.

Discovery effort should be proportional to the task.

### 14.1 Quick tasks

Prefer existing knowledge and localized discovery.

Do not perform broad repository analysis without a concrete reason.

### 14.2 Standard tasks

Investigate affected components and relevant dependencies.

### 14.3 Deep tasks

Expand investigation according to architectural risk, uncertainty, and verification requirements.

### 14.4 Explore tasks

Prioritize investigation and evidence gathering without assuming implementation is authorized.

### 14.5 Escalation

A task may require deeper discovery when new evidence reveals unexpected dependencies or risks.

Escalation must remain visible in the task plan.

---

## 15. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Incremental discovery

AEW must not require exhaustive repository analysis before every task.

### INV-002 — Task relevance

Discovery must prioritize information relevant to the current engineering objective.

### INV-003 — Evidence-backed knowledge

Discovered assertions must retain identifiable supporting evidence.

### INV-004 — Revision applicability

Knowledge must remain associated with the repository observation against which it was established.

### INV-005 — Targeted invalidation

Changes should invalidate affected knowledge regions rather than indiscriminately invalidating the entire Project Brain.

### INV-006 — Historical immutability

Invalidation must not mutate published assertions or snapshots.

### INV-007 — Conservative reuse

Existing assertions may be reused only when their continued applicability is supported.

### INV-008 — Unknown remains unknown

Uncertain freshness or incomplete dependency coverage must not be represented as verified current knowledge.

### INV-009 — Dependency-aware propagation

Invalidation must consider relevant dependency relationships and their semantics.

### INV-010 — Bounded investigation

Discovery should stop when sufficient evidence exists for the next engineering decision or when its budget is exhausted.

### INV-011 — Depth independence

Discovery stage must not be confused with investigation depth.

### INV-012 — Freshness independence

Investigation depth must not imply current applicability.

### INV-013 — Context consistency

Context Packages must preserve coherent snapshot and revision identity.

### INV-014 — No implicit authority

Discovered knowledge does not independently authorize implementation.

---

## 16. Alternatives Considered

The following alternatives summarize the tradeoffs relevant to the accepted architecture.

### 16.1 Full repository analysis before every task

**Advantages**

- Broad initial coverage.
- Potentially fewer unknown regions.

**Disadvantages**

- High latency.
- Repeated work.
- Expensive for large repositories.
- Disproportionate overhead for small tasks.

**Disposition:** Rejected as a universal requirement.

### 16.2 Rebuild the entire Project Brain after every change

**Advantages**

- Simpler conceptual invalidation model.
- Avoids some incremental update complexity.

**Disadvantages**

- Expensive.
- Unnecessary rediscovery.
- Poor scalability.
- Increased risk of interrupting unrelated engineering work.

**Disposition:** Rejected as the default maintenance strategy.

### 16.3 Never invalidate stored knowledge

**Advantages**

- Minimal maintenance overhead.
- Fast retrieval.

**Disadvantages**

- Stale knowledge accumulates.
- Architectural assumptions become unreliable.
- Context Packages may contain incorrect current-state claims.

**Disposition:** Rejected.

### 16.4 Invalidate only directly changed files

**Advantages**

- Simple implementation.
- Narrow invalidation frontier.

**Disadvantages**

- Misses dependent contracts.
- Misses interface consumers.
- Misses configuration-driven relationships.
- Can incorrectly preserve stale behavioral assertions.

**Disposition:** Insufficient as the complete strategy.

### 16.5 Traverse every reachable dependency

**Advantages**

- Broad dependency coverage.

**Disadvantages**

- Potentially unbounded investigation.
- Excessive work in highly connected graphs.
- Poor proportionality to task risk.

**Disposition:** Rejected as the default discovery rule.

---

## 17. Consequences

### 17.1 Positive consequences

- Lower repeated investigation cost.
- Faster task preparation.
- Better knowledge reuse.
- More relevant Context Packages.
- Improved scalability for large repositories.
- Reduced unnecessary graph rebuilding.
- More accurate freshness reporting.
- Better support for heterogeneous projects.
- Adaptive investigation proportional to risk.

### 17.2 Costs

- Change detection logic.
- Dependency-aware invalidation.
- Applicability tracking.
- Discovery planning.
- Coverage metadata.
- Reconciliation of uncertain assertions.
- Additional testing for stale knowledge.

### 17.3 Risks

**Under-invalidation**

Relevant dependencies may be missed.

Mitigation: Preserve uncertainty and expand the frontier when evidence warrants it.

**Over-invalidation**

Too much knowledge may be marked stale.

Mitigation: Use evidence-based applicability and scoped dependency relationships.

**Discovery loops**

Investigation may repeatedly revisit the same regions.

Mitigation: Track completed discovery, progress, and budgets.

**False confidence**

A narrow investigation may be presented as comprehensive.

Mitigation: Explicit coverage and uncertainty reporting.

**Stale evidence reuse**

An assertion may be reused despite a relevant change.

Mitigation: Verify source applicability before reuse.

---

## 18. Implementation Guidance

### 18.1 Initial milestone

Staged discovery and targeted invalidation should be introduced during M2.

### 18.2 Minimum viable implementation

The initial implementation should support:

- Repository revision comparison.
- Changed-path detection.
- Mapping changed paths to knowledge regions.
- Direct evidence invalidation.
- Basic dependency frontier expansion.
- Assertion applicability tracking.
- Targeted rediscovery.
- Snapshot membership construction.
- Coverage reporting.

Advanced semantic impact analysis may be added later.

### 18.3 Suggested logical interfaces

Possible operations include:

```text
orient_repository(repository, revision)

discover_task_regions(task, snapshot)

expand_dependency_frontier(regions, budget)

detect_repository_changes(previous, current)

identify_affected_assertions(changes, snapshot)

plan_targeted_revalidation(affected_assertions)

publish_updated_snapshot(revalidated_assertions)
```

These are conceptual operations, not mandatory function signatures.

### 18.4 Persistence

Discovery state should use the Project Brain's existing persistence model.

Avoid creating an unrelated mutable knowledge store.

### 18.5 Idempotency

Repeated discovery against the same evidence should avoid creating unnecessary duplicate assertions.

Stable identity and content-based deduplication may be used where appropriate.

### 18.6 Failure handling

If discovery fails or is interrupted:

- Preserve previously published snapshots.
- Retain partial investigation state separately.
- Report unresolved regions.
- Avoid publishing incomplete findings as verified current knowledge.

### 18.7 Performance

The implementation should measure:

- Discovery latency.
- Number of regions inspected.
- Assertions reused.
- Assertions invalidated.
- Assertions revalidated.
- Dependency expansion cost.

Performance optimization must not weaken freshness guarantees.

---

## 19. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Small localized task | Only relevant regions investigated |
| Unchanged repository | Applicable knowledge reused |
| Single source file changed | Directly affected assertions reassessed |
| Public interface changed | Relevant dependent regions considered |
| Unrelated documentation changed | Unaffected source assertions remain reusable |
| Dependency manifest changed | Relevant technology profile assertions reassessed |
| Rename detected | Entity continuity evaluated rather than assumed |
| Unknown dependency relationship | Uncertainty preserved |
| Partial discovery | Coverage reported accurately |
| Discovery budget exhausted | Investigation stops with unresolved questions |
| Concurrent investigations | Published snapshots remain coherent |
| Historical snapshot queried | Original assertions remain unchanged |
| Assertion no longer applicable | Omitted from newer current snapshot |
| Context Package generated | Uses coherent snapshot membership |
| Deep historical knowledge reused | Freshness independently verified |
| Repeated discovery | No unnecessary duplicate assertions |
| Interrupted discovery | No partially published verified snapshot |

### 19.1 Test isolation

Tests should use disposable Git repositories and isolated Project Brain databases.

### 19.2 Correctness testing

Tests must verify both:

- Knowledge that should be invalidated.
- Knowledge that should remain reusable.

An invalidation system that marks everything stale is conservative but does not satisfy the targeted maintenance objective.

### 19.3 Evidence

Verification must use observed behavior and reproducible test results.

---

## 20. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Establishes Project Brain persistence.

**ADR-003 — Revision-Scoped Graph Snapshots**

Defines immutable assertions and coherent snapshots.

**ADR-004 — Workspace Consistency**

Defines committed and uncommitted workspace observations.

**ADR-006 — Per-Project Intelligence Profiles**

Defines project characteristics maintained through discovery.

**ADR-008 — Progressive Knowledge Depth**

Defines investigation depth independently of discovery stage.

**ADR-009 — Immutable Context Packages**

Defines task-relevant knowledge packaging.

**ADR-012 — Adaptive Planning**

Defines proportional investigation and planning behavior.

### Related contracts

- `contracts/context.schema.json`
- `contracts/task.schema.json`

Additional internal discovery and invalidation contracts may be introduced during M2 if justified by implementation requirements.

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 21. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact knowledge region identity scheme.
2. The algorithm for dependency frontier expansion.
3. The initial relationship types used for invalidation.
4. The method for measuring discovery completeness.
5. The criteria for reusing assertions across revisions.
6. The strategy for handling generated files.
7. The discovery budget model.
8. The representation of partial investigation state.
9. The policy for resolving conflicting discovery results.
10. The thresholds for escalating to broader investigation.

These questions should be resolved through implementation evidence and concrete project requirements.

They must preserve the architectural invariants established above.

---

## 22. Acceptance and Compliance

ADR-007 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Repository discovery is incremental.
- Task relevance drives investigation.
- Existing applicable knowledge is reused.
- Changed evidence triggers targeted reassessment.
- Relevant dependencies influence invalidation.
- Historical snapshots remain immutable.
- Incomplete coverage and uncertain freshness remain visible.
- Discovery budgets are respected.
- Context Packages receive coherent knowledge.
- Unrelated knowledge is not unnecessarily invalidated.

Compliance requires observed test evidence.

The existence of this document does not establish that the implementation already satisfies these requirements.

---

## 23. Decision Summary

AEW uses staged, task-driven discovery to acquire project knowledge incrementally.

Discovery begins with lightweight repository orientation, expands through task-relevant components and dependencies, and deepens only when justified by risk or uncertainty.

Repository changes trigger targeted reassessment of affected assertions and dependency regions.

Previously published assertions and snapshots remain immutable.

Knowledge may be reused across revisions when its continued applicability is supported by evidence.

**AEW should investigate what matters, preserve what remains valid, and revisit only what the evidence requires.**