# ADR-008 — Progressive Knowledge Depth and Independent Freshness

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Knowledge depth, investigation completeness, freshness, evidence coverage, and adaptive context acquisition  
**Related milestones:** M2 — Project Brain Foundation; M3 — Context Packages; M4 — Adaptive Planning

---

## 1. Context

The Adaptive Engineering Workbench (AEW) maintains persistent knowledge about software repositories through its Project Brain.

This knowledge is acquired incrementally, as established by ADR-007, and stored through revision-scoped graph snapshots, as established by ADR-003.

However, not all knowledge has the same level of detail.

AEW may know that a component exists without understanding its interfaces.

It may understand the interfaces without understanding the component's behavior.

It may understand ordinary behavior without having investigated concurrency, failure handling, security boundaries, or domain invariants.

Treating all discovered knowledge as equally complete would produce misleading engineering assessments.

A second problem arises when knowledge becomes stale.

A detailed investigation may remain historically accurate while no longer describing the current repository.

Conversely, a recent inspection may establish that a component exists without providing meaningful behavioral understanding.

AEW therefore requires two independent dimensions:

1. **Knowledge depth:** How thoroughly a region has been investigated.
2. **Knowledge freshness:** Whether the evidence supporting that knowledge remains applicable.

These dimensions must not be collapsed into a single confidence score.

The system must also distinguish investigation depth from evidence quality, verification status, and coverage.

---

## 2. Decision

AEW will maintain **progressive knowledge depth levels D0 through D3 for relevant project regions**, with freshness tracked independently.

Knowledge acquisition should deepen only when justified by task requirements, risk, uncertainty, or explicit investigation objectives.

The Project Brain must preserve the depth achieved, the evidence supporting it, the repository observation to which it applies, and any known limitations.

### 2.1 Core requirements

AEW must:

1. Represent knowledge depth using D0–D3.
2. Track freshness independently.
3. Associate depth claims with evidence.
4. Support different depths across repository regions.
5. Allow targeted deepening without full-repository analysis.
6. Preserve historical depth information.
7. Report incomplete coverage.
8. Avoid treating inferred knowledge as verified understanding.
9. Support task-specific depth requirements.
10. Reassess freshness when relevant evidence changes.

### 2.2 Fundamental distinction

**Depth answers:** How much has AEW investigated?

**Freshness answers:** Does the investigation still apply?

Neither dimension independently establishes correctness, authority, or completeness.

---

## 3. Knowledge Depth Model

AEW uses four progressive depth levels.

| Level | Name | Primary understanding |
|---|---|---|
| D0 | Discovery | What exists and where |
| D1 | Structural | How components are organized and connected |
| D2 | Behavioral | How relevant functionality operates |
| D3 | Deep | Invariants, edge cases, failure behavior, and complex semantics |

Depth is associated with a defined knowledge region and investigation scope.

It is not necessarily a property of the entire repository.

---

## 4. D0 — Discovery

### 4.1 Purpose

D0 establishes basic awareness of a repository region.

It answers questions such as:

- Does this component exist?
- Where is it located?
- What language is it written in?
- What appears to be its general responsibility?
- Which obvious configuration or build files are associated with it?

### 4.2 Typical evidence

Examples include:

- File paths.
- Directory structure.
- Source declarations.
- Dependency manifests.
- Configuration files.
- Repository documentation.

### 4.3 Expected output

A D0 investigation may establish:

- Component identity.
- Source location.
- Language.
- Basic classification.
- Initial evidence references.
- Known uncertainty.

### 4.4 Limitations

D0 does not establish:

- Complete dependency relationships.
- Detailed behavior.
- Runtime correctness.
- Domain invariants.
- Failure semantics.
- Security properties.

### 4.5 Example

```text
Region: CustomerService
Depth: D0

Known:
    Class exists.
    Located in src/customer/.
    Written in Java.

Unknown:
    Dependencies.
    Runtime behavior.
    Error handling.
    Invariants.
```

A D0 result must not be presented as a complete architectural understanding.

---

## 5. D1 — Structural Understanding

### 5.1 Purpose

D1 establishes the relevant organization and relationships of a component.

It answers questions such as:

- What interfaces does the component expose?
- What does it depend on?
- Which components call it?
- Which configuration controls it?
- Which tests are associated with it?
- How does it fit into the surrounding architecture?

### 5.2 Typical evidence

Examples include:

- Method signatures.
- Imports.
- Interface declarations.
- Dependency injection configuration.
- Build dependencies.
- Call relationships.
- Test references.
- API definitions.

### 5.3 Expected output

A D1 investigation may establish:

- Relevant public interfaces.
- Structural dependencies.
- Component relationships.
- Configuration relationships.
- Associated tests.
- Known architectural boundaries.

### 5.4 Limitations

D1 does not necessarily establish:

- Complete runtime behavior.
- Error propagation.
- Transactional semantics.
- Concurrency behavior.
- Hidden side effects.
- Domain invariants.

### 5.5 Example

```text
Region: CustomerService
Depth: D1

Known:
    Implements CustomerOperations.
    Depends on CustomerRepository.
    Called by CustomerController.
    Tested by CustomerServiceTest.

Unknown:
    Complete null-handling behavior.
    Transaction boundaries.
    Concurrency assumptions.
```

Structural relationships must retain supporting evidence.

---

## 6. D2 — Behavioral Understanding

### 6.1 Purpose

D2 establishes how relevant functionality operates.

It answers questions such as:

- What happens when a method is called?
- How does data move through the component?
- What conditions control execution?
- What side effects occur?
- How are errors handled?
- What outputs are produced for relevant inputs?

### 6.2 Typical evidence

Examples include:

- Source-code control flow.
- Data transformations.
- Error-handling paths.
- Test behavior.
- Execution traces.
- Configuration-dependent behavior.
- Database operations.
- External service interactions.

### 6.3 Expected output

A D2 investigation may establish:

- Relevant control flow.
- Data flow.
- Input and output behavior.
- Important side effects.
- Error paths.
- Relevant runtime dependencies.
- Behavioral test coverage.

### 6.4 Limitations

D2 does not automatically establish:

- Exhaustive edge-case coverage.
- Absence of race conditions.
- Security correctness.
- Complete domain invariants.
- Correctness under all failure conditions.

### 6.5 Example

```text
Region: CustomerService
Depth: D2

Known:
    Retrieves customer by identifier.
    Maps repository results.
    Returns not-found for missing records.
    Propagates selected repository failures.

Unknown:
    Behavior under concurrent updates.
    All transaction isolation assumptions.
    Security-sensitive edge conditions.
```

Behavioral conclusions must remain scoped to the investigated paths and evidence.

---

## 7. D3 — Deep Semantic and Invariant Analysis

### 7.1 Purpose

D3 investigates complex behavior, constraints, and failure conditions.

It is appropriate when a task involves substantial risk, uncertainty, or architectural sensitivity.

D3 may investigate:

- Domain invariants.
- Concurrency.
- Race conditions.
- Transaction boundaries.
- Security boundaries.
- Failure recovery.
- State-machine correctness.
- Data consistency.
- Resource ownership.
- Backward compatibility.
- Complex integration semantics.

### 7.2 Typical evidence

Examples include:

- Detailed control-flow analysis.
- State-transition analysis.
- Concurrency reasoning.
- Transactional behavior.
- Security-sensitive source paths.
- Failure injection.
- Property-based tests.
- Integration tests.
- Historical defects.
- Relevant architectural decisions.

### 7.3 Expected output

A D3 investigation may establish:

- Explicit invariants.
- Critical preconditions.
- Critical postconditions.
- Failure-mode analysis.
- Relevant edge cases.
- Concurrency assumptions.
- Security-sensitive relationships.
- Known limitations and unresolved risks.

### 7.4 Limitations

D3 does not imply formal proof of correctness.

A D3 investigation may remain incomplete.

Some properties may require runtime environments, specialized tooling, formal methods, or evidence that is unavailable.

### 7.5 Example

```text
Region: CustomerService
Depth: D3

Investigated:
    Null-handling invariants.
    Transaction boundaries.
    Concurrent update behavior.
    Repository failure propagation.
    Backward compatibility.
    Relevant security constraints.

Remaining uncertainty:
    Production database isolation behavior
    has not been independently verified.
```

A region may be classified as D3 for the investigated scope while retaining unresolved questions.

AEW must not represent D3 as a guarantee of complete correctness.

---

## 8. Depth Is Scoped

Knowledge depth must be associated with the actual subject and investigation boundary.

### 8.1 Regional depth

Different repository regions may have different depths.

For example:

```text
Repository
│
├── Authentication
│   └── D3
│
├── Customer API
│   └── D2
│
├── Reporting
│   └── D1
│
└── Legacy Import
    └── D0
```

This is a valid Project Brain state.

AEW does not need to investigate every component to D3.

### 8.2 Subregional depth

A component may have different depth coverage for different behaviors.

For example:

```text
CustomerService

Customer lookup:
    D3

Customer update:
    D2

Customer export:
    D0
```

A single component-level depth value must not conceal important differences in coverage.

### 8.3 Aggregation

A summary depth for a larger region may be useful.

However, aggregation must not imply that every subregion has reached the same level.

If a region contains D0 and D3 knowledge, reporting the entire region as uniformly D3 is misleading.

### 8.4 Evidence coverage

Depth claims must identify which behaviors, relationships, or constraints were actually investigated.

A depth label without coverage information is insufficient for high-risk engineering decisions.

---

## 9. Freshness Model

Freshness represents the applicability of knowledge to a repository observation.

### 9.1 Initial freshness states

The logical model should support:

| State | Meaning |
|---|---|
| Current | Evidence applicability established for the target observation |
| Stale | Relevant evidence changed or applicability is known to be outdated |
| Unknown | Applicability has not been established |
| Not applicable | Knowledge does not apply to the target observation |

These states describe applicability, not confidence or correctness.

### 9.2 Current

Knowledge is current when sufficient evidence establishes that it applies to the target repository observation.

A matching Git commit may provide strong revision identity, but uncommitted workspace modifications must also be considered where relevant.

### 9.3 Stale

Knowledge is stale when relevant evidence has changed or a known condition invalidates its applicability.

Historical knowledge remains available.

It must not be silently promoted into current context.

### 9.4 Unknown

Freshness is unknown when applicability cannot be established.

Unknown must not be interpreted as current.

### 9.5 Not applicable

Knowledge may be valid historically or in another context but irrelevant to the current repository observation.

This differs from stale knowledge.

### 9.6 Freshness evidence

Freshness assessment may consider:

- Repository revisions.
- Relevant file content identities.
- Dependency changes.
- Configuration changes.
- Workspace observations.
- Targeted revalidation.
- Verification results.

The exact freshness calculation is an implementation detail.

---

## 10. Depth and Freshness Independence

Depth and freshness must remain separate dimensions.

### 10.1 Example matrix

| Knowledge | Depth | Freshness | Interpretation |
|---|---|---|---|
| Newly discovered component | D0 | Current | Exists, limited understanding |
| Recently analyzed data flow | D2 | Current | Behavior investigated and applicable |
| Historical concurrency analysis | D3 | Stale | Deep knowledge, no longer established as current |
| Old interface documentation | D1 | Unknown | Structural knowledge requiring validation |
| Removed component | D2 | Not applicable | Historical behavior, not part of current revision |

### 10.2 Prohibited inference

AEW must not infer:

- D3 means current.
- Current means D3.
- High confidence means verified.
- Recent observation means complete.
- Historical verification means current verification.

### 10.3 Independent transitions

A region may become stale without losing its historical depth.

For example:

```text
Before change:
    Depth: D3
    Freshness: Current

After relevant change:
    Depth: D3
    Freshness: Stale

After targeted revalidation:
    Depth: D3
    Freshness: Current
```

The final transition requires supporting evidence.

It must not occur automatically.

---

## 11. Verification and Confidence

Depth, freshness, verification, and confidence describe different properties.

### 11.1 Depth

How thoroughly the relevant subject was investigated.

### 11.2 Freshness

Whether the evidence remains applicable.

### 11.3 Verification

Whether a particular claim was checked through an appropriate procedure or authoritative source.

### 11.4 Confidence

An estimate of uncertainty associated with an assertion or interpretation.

Confidence may help prioritize investigation.

It must not replace evidence or verification.

### 11.5 Example

A static analysis may identify a possible race condition.

The finding could be:

```text
Depth: D3
Freshness: Current
Verification: Provisional
Confidence: Medium
```

The analysis is deep and based on current code, but the suspected race condition has not been demonstrated.

AEW must preserve these distinctions.

---

## 12. Progressive Deepening

AEW should increase investigation depth only when justified.

### 12.1 Task requirements

Depth requirements may depend on:

- Scope.
- Risk.
- Uncertainty.
- Architectural impact.
- Domain sensitivity.
- Security implications.
- Concurrency.
- Verification complexity.
- Existing knowledge coverage.

### 12.2 Quick tasks

A localized, low-risk task may require D1 or D2 understanding of a small region.

D3 must not be mandatory solely because it exists as a supported level.

### 12.3 Standard tasks

Ordinary feature or maintenance work may require structural and behavioral understanding of relevant components.

### 12.4 Deep tasks

High-risk or cross-cutting work may require D3 investigation of selected boundaries.

### 12.5 Explore tasks

An Explore task may deepen knowledge without authorizing implementation.

### 12.6 Escalation

New evidence may justify deeper investigation.

For example:

```text
Initial task:
    Fix null mapping.

Initial depth:
    D2

New finding:
    Mapping behavior participates in
    transaction retry logic.

Escalation:
    Investigate retry invariants at D3.
```

The escalation should be reflected in the task assessment when material.

---

## 13. Depth Requirements and Stopping Criteria

AEW must avoid unbounded investigation.

### 13.1 Required depth

A task may define a target depth for specific regions or questions.

For example:

```text
CustomerMapper:
    D2 for null-handling behavior.

CustomerRepository:
    D1 for dependency relationships.

TransactionCoordinator:
    D3 for retry and idempotency invariants.
```

### 13.2 Evidence threshold

A depth level is achieved only when sufficient evidence supports the relevant investigation objectives.

Reading a file does not automatically establish D2.

Executing a test does not automatically establish D3.

### 13.3 Stopping conditions

Deepening may stop when:

- Required questions have been answered.
- Relevant invariants are identified.
- Sufficient evidence exists for the next decision.
- Remaining uncertainties are documented.
- Additional analysis has low expected value.
- The investigation budget is exhausted.

### 13.4 Budget exhaustion

If a budget is exhausted before the required depth is achieved, AEW must report the shortfall.

It must not silently assign the requested depth.

### 13.5 Proportionality

The goal is sufficient understanding for safe engineering decisions, not maximum depth everywhere.

---

## 14. Project Brain Integration

ADR-003 establishes immutable assertions and revision-scoped snapshots.

Depth and freshness metadata must integrate with that model.

### 14.1 Assertion-level information

Individual assertions may retain:

- Investigation depth.
- Evidence.
- Verification status.
- Revision applicability.
- Uncertainty.

### 14.2 Region-level summaries

Region summaries may aggregate available knowledge.

However, they must preserve coverage limitations.

### 14.3 Immutable history

A previously published assertion must not be modified merely because its freshness changes relative to a newer revision.

Freshness may be represented through new applicability records, derived assessments, or new snapshot membership.

### 14.4 Snapshot consistency

Depth and freshness summaries must be associated with coherent snapshot observations.

### 14.5 Revalidation

Targeted revalidation may establish that existing assertions remain applicable.

Such revalidation must preserve historical provenance.

---

## 15. Staged Discovery Integration

ADR-007 defines staged discovery.

Discovery stage and knowledge depth are related but not equivalent.

### 15.1 Discovery stages

- S0 — Repository orientation.
- S1 — Task-relevant discovery.
- S2 — Dependency expansion.
- S3 — Focused deep investigation.

### 15.2 Distinct responsibilities

Discovery stages describe the investigation process.

Knowledge depth describes the understanding established.

### 15.3 Example

S2 dependency expansion may produce D1 structural knowledge for several components.

S3 focused investigation may produce D3 knowledge for one transaction boundary.

The stage reached does not automatically establish the depth achieved.

### 15.4 Targeted invalidation

When relevant evidence changes, freshness must be reassessed.

Historical depth remains recorded.

---

## 16. Context Package Integration

ADR-009 defines immutable Context Packages.

Context Packages must preserve relevant depth, freshness, coverage, and uncertainty information.

### 16.1 Required context

A Context Package should communicate:

- Which regions are included.
- What depth has been achieved.
- Whether the knowledge is current.
- Which evidence supports the claims.
- Which questions remain unresolved.
- Which relevant regions were not investigated.

### 16.2 Task relevance

Context selection should prioritize the knowledge needed for the current task.

A package should not include every D3 investigation merely because it is detailed.

### 16.3 Stale knowledge

Stale knowledge may be included as historical context when useful.

It must be explicitly identified as stale.

### 16.4 Context expansion

If a task requires deeper understanding, AEW may generate a new Context Package after additional investigation.

The original package remains immutable.

### 16.5 Revision consistency

Expanded context must preserve coherent revision applicability.

A deeper investigation at a newer commit cannot silently be merged into an older package as if both observations represented one repository state.

---

## 17. Adaptive Planning Integration

ADR-012 defines adaptive planning.

Knowledge depth and freshness influence task assessment.

### 17.1 Risk assessment

A high-risk task involving a D0 region may require additional investigation.

A low-risk task involving a current D2 region may require little additional discovery.

### 17.2 Uncertainty assessment

Missing behavioral knowledge or stale evidence may increase uncertainty.

### 17.3 Planning profile selection

Depth and freshness may inform Quick, Standard, Deep, or Explore classification.

They must not be the sole determinants.

### 17.4 Verification planning

A deep investigation may identify important tests and invariants.

However, the existence of D3 knowledge does not prove that current tests pass.

### 17.5 Work Unit boundaries

Different regions may require different investigation depths within the same Work Unit.

---

## 18. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Progressive depth

AEW supports D0, D1, D2, and D3 knowledge levels.

### INV-002 — Independent freshness

Freshness must be tracked separately from depth.

### INV-003 — Scoped depth

Depth applies to defined knowledge regions and investigation boundaries.

### INV-004 — Evidence-backed classification

Depth claims require supporting investigation evidence.

### INV-005 — No automatic completeness

A depth label does not establish complete understanding of an entire component or repository.

### INV-006 — Historical depth preservation

Knowledge becoming stale does not erase its historical investigation depth.

### INV-007 — Unknown is not current

Unknown freshness must not be represented as current.

### INV-008 — No automatic verification

Depth and freshness do not independently establish empirical verification.

### INV-009 — Proportional investigation

AEW must not require D3 analysis for every task.

### INV-010 — Targeted deepening

Investigation depth should increase where justified by task relevance, risk, or uncertainty.

### INV-011 — Budget honesty

Unachieved depth requirements must remain visible when investigation stops.

### INV-012 — Snapshot consistency

Depth and freshness assessments must preserve coherent repository revision applicability.

### INV-013 — Context transparency

Context Packages must retain relevant depth, freshness, coverage, and uncertainty information.

### INV-014 — No authority escalation

Deep or current knowledge does not independently authorize implementation.

---

## 19. Alternatives Considered

The following alternatives summarize the tradeoffs relevant to the accepted architecture.

### 19.1 Binary known/unknown classification

**Advantages**

- Simple persistence.
- Easy retrieval.

**Disadvantages**

- Cannot distinguish superficial discovery from behavioral understanding.
- Produces misleading context.
- Weak support for proportional investigation.

**Disposition:** Rejected as the complete knowledge model.

### 19.2 Single confidence score

**Advantages**

- Compact representation.
- Easy ranking.

**Disadvantages**

- Conflates depth, freshness, evidence, and uncertainty.
- Difficult to interpret.
- May create false precision.

**Disposition:** Rejected as a substitute for independent dimensions.

### 19.3 Maximum-depth analysis everywhere

**Advantages**

- Potentially broad understanding.
- Fewer shallow regions.

**Disadvantages**

- Excessive cost.
- Slow task preparation.
- Unnecessary analysis.
- Poor scalability.

**Disposition:** Rejected as the default strategy.

### 19.4 Reset depth when knowledge becomes stale

**Advantages**

- Simple current-state summaries.

**Disadvantages**

- Destroys useful historical information.
- Causes unnecessary rediscovery.
- Confuses applicability with investigation effort.

**Disposition:** Rejected.

### 19.5 Assign depth based on tool usage

**Advantages**

- Easy automation.
- Simple heuristics.

**Disadvantages**

- Reading files does not prove understanding.
- Running tests does not prove invariant coverage.
- Tool activity may not produce useful evidence.

**Disposition:** Insufficient.

---

## 20. Consequences

### 20.1 Positive consequences

- More accurate representation of project understanding.
- Lower unnecessary investigation cost.
- Better task-specific context.
- Explicit knowledge limitations.
- Improved planning decisions.
- Reuse of historical deep investigations.
- Better freshness management.
- More reliable identification of investigation gaps.
- Support for complex and heterogeneous repositories.

### 20.2 Costs

- Additional metadata.
- Evidence-to-depth mapping.
- Coverage tracking.
- Freshness reassessment.
- Region-level aggregation.
- More sophisticated context selection.
- Verification of depth classifications.

### 20.3 Risks

**Depth inflation**

AEW may assign D3 without sufficient investigation.

Mitigation: Require evidence and scoped coverage.

**False freshness**

Old assertions may be treated as current.

Mitigation: Revision-aware applicability checks.

**Over-investigation**

AEW may deepen unrelated regions unnecessarily.

Mitigation: Task-driven depth requirements.

**Under-investigation**

AEW may stop before resolving critical uncertainty.

Mitigation: Risk-sensitive stopping criteria and explicit unresolved questions.

**Misleading summaries**

Aggregated depth may conceal shallow subregions.

Mitigation: Preserve coverage boundaries.

---

## 21. Implementation Guidance

### 21.1 Initial milestone

Depth and freshness tracking should be introduced during M2.

### 21.2 Minimum viable model

The initial implementation should support:

- Region identity.
- Depth classification.
- Freshness classification.
- Repository observation identity.
- Evidence references.
- Coverage description.
- Verification status.
- Unresolved uncertainties.

### 21.3 Suggested logical interfaces

Possible operations include:

```text
assess_region_depth(region, evidence)

assess_knowledge_freshness(assertion, revision)

identify_depth_gaps(task, snapshot)

plan_targeted_deepening(regions, required_depth)

record_investigation_result(region, depth, evidence)

summarize_knowledge_coverage(snapshot, scope)
```

These are conceptual operations, not mandatory function signatures.

### 21.4 Storage integration

Use the Project Brain's assertion and snapshot model.

Avoid introducing a separate mutable depth database that can contradict published snapshots.

### 21.5 Depth validation

Depth classification should be based on evidence coverage rather than the number of files read or tools invoked.

### 21.6 Freshness validation

Freshness should be established through repository and evidence applicability checks.

### 21.7 Performance

AEW should measure:

- Investigation time.
- Regions deepened.
- Knowledge reused.
- Revalidation cost.
- Unresolved depth gaps.
- Context retrieval cost.

Performance optimization must not weaken evidence requirements.

---

## 22. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Component existence discovered | D0 may be established |
| Interfaces and dependencies inspected | D1 may be established |
| Relevant control flow analyzed | D2 may be established |
| Invariants and failure paths investigated | D3 may be established for the investigated scope |
| File merely opened | No automatic D2 classification |
| Test command discovered | No automatic verification claim |
| D3 region becomes stale | D3 history preserved; freshness changes |
| D0 region freshly inspected | Current D0 represented correctly |
| Partial D3 investigation | Coverage limitations retained |
| Different subregions have different depths | Distinctions preserved |
| Knowledge from earlier commit reused | Applicability verified |
| Relevant evidence changes | Freshness reassessed |
| Unrelated evidence changes | Applicable knowledge may remain current |
| Investigation budget exhausted | Required depth shortfall reported |
| Context Package generated | Depth and freshness preserved |
| Context expanded after deeper investigation | Original package unchanged |
| Snapshot queried historically | Original depth and evidence remain reproducible |
| Provisional security finding | Not automatically treated as verified |
| Unknown freshness | Not presented as current |

Tests should use isolated Project Brain databases and disposable repository fixtures.

Verification must rely on observed behavior.

---

## 23. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Establishes Project Brain persistence.

**ADR-003 — Revision-Scoped Graph Snapshots**

Defines immutable assertions and coherent repository observations.

**ADR-006 — Per-Project Intelligence Profiles**

Defines evidence-backed project characterization.

**ADR-007 — Staged Discovery and Targeted Invalidation**

Defines incremental investigation and knowledge maintenance.

**ADR-009 — Immutable Context Packages**

Defines task-relevant knowledge packaging.

**ADR-012 — Adaptive Planning**

Uses knowledge coverage and uncertainty to determine proportional planning.

### Related contracts

- `contracts/context.schema.json`
- `contracts/task.schema.json`

Additional internal knowledge coverage contracts may be introduced during M2 when justified.

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 24. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact persistence representation of region-level depth.
2. The criteria for aggregating depth across subregions.
3. The evidence thresholds for each depth level.
4. The precise freshness transition mechanism.
5. The algorithm for selecting targeted deepening.
6. The initial supported knowledge region granularity.
7. The representation of incomplete D3 coverage.
8. The policy for handling contradictory evidence.
9. The performance budget for depth reassessment.
10. The compact depth/freshness representation used by AI skills.

These details should be resolved during implementation using concrete requirements and verification evidence.

They must preserve the invariants established by this ADR.

---

## 25. Acceptance and Compliance

ADR-008 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- D0–D3 depth levels are represented.
- Freshness is independent of depth.
- Depth claims retain evidence and coverage.
- Different regions may have different depths.
- Historical depth is preserved when knowledge becomes stale.
- Unknown freshness is not treated as current.
- Depth does not automatically imply verification.
- Task requirements drive proportional investigation.
- Context Packages preserve depth and freshness.
- Revision consistency is maintained.

Compliance requires observed verification evidence.

The existence of this ADR does not establish that the implementation already satisfies these requirements.

---

## 26. Decision Summary

AEW represents project knowledge using progressive investigation depths D0 through D3.

D0 establishes existence and location.

D1 establishes structure and relationships.

D2 establishes relevant behavior.

D3 investigates complex semantics, invariants, edge cases, and failure conditions.

Freshness is tracked independently and describes whether the knowledge remains applicable to the target repository observation.

Depth, freshness, verification, confidence, and coverage must remain distinguishable.

Investigation should deepen only where justified by task relevance, risk, uncertainty, and evidence requirements.

**AEW must know both how deeply a component has been investigated and whether that understanding still applies.**