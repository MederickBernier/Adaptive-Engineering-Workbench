# ADR-006 — Per-Project Intelligence Profiles

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Project characterization, technology discovery, engineering conventions, architectural patterns, and evidence-backed repository intelligence  
**Related milestones:** M2 — Project Brain Foundation; M3 — Context Packages; M4 — Adaptive Planning

---

## 1. Context

The Adaptive Engineering Workbench (AEW) is intended to operate across different programming languages, frameworks, development environments, and architectural styles.

Repositories may contain:

- A single programming language.
- Multiple programming languages.
- Modern frameworks.
- Legacy systems.
- Monolithic applications.
- Distributed services.
- Build scripts and infrastructure definitions.
- Generated code.
- Custom development conventions.
- Multiple independent applications within a monorepo.

An engineering assistant that assumes a universal project structure can make incorrect decisions.

For example, a Java application may use Maven, Gradle, or a custom build system.

A PHP application may use Laravel, Symfony, a custom framework, or procedural code.

A COBOL repository may depend on JCL, copybooks, DB2, CICS, and external mainframe deployment processes.

Even repositories using the same language can have substantially different architectural constraints.

AEW therefore needs to discover the actual characteristics of each project rather than impose a predetermined technology profile.

This knowledge must remain persistent, evidence-backed, revision-aware, and incrementally maintainable.

---

## 2. Decision

AEW will maintain a **Project Intelligence Profile** for each project.

The profile describes the repository's observed technical characteristics, engineering conventions, and relevant architectural structure.

It is maintained within the project's Project Brain and associated with appropriate repository observations.

The profile must be derived from evidence.

It must distinguish verified observations, provisional conclusions, conflicting evidence, and unknown characteristics.

### 2.1 Core responsibilities

The Project Intelligence Profile must support:

1. Technology discovery.
2. Build and dependency system discovery.
3. Testing and verification discovery.
4. Repository organization discovery.
5. Engineering convention discovery.
6. Architectural pattern discovery.
7. Environment and deployment discovery.
8. Evidence and provenance tracking.
9. Revision applicability.
10. Incremental updates.

### 2.2 Adaptive behavior

AEW may use the profile to guide:

- Repository investigation.
- Context selection.
- Test selection.
- Implementation planning.
- Code generation conventions.
- Work Unit boundaries.
- Risk assessment.
- Verification recommendations.

The profile informs engineering decisions.

It does not independently authorize implementation or override repository policy.

### 2.3 No universal technology assumptions

AEW must not assume that a repository uses a framework, test runner, package manager, or architecture solely because a particular language is detected.

Such characteristics require independent evidence.

---

## 3. Profile Identity and Scope

### 3.1 Project identity

Each profile belongs to an identified project within the Project Brain.

The project identity must remain distinct from the current repository path.

A repository may be relocated without necessarily becoming a new project.

### 3.2 Repository identity

The profile must identify the repository or repositories to which its observations apply.

A profile must not silently combine unrelated repositories.

### 3.3 Revision context

Source-derived profile assertions must retain their repository revision applicability.

A profile observed at commit A must not automatically be considered verified at commit B.

### 3.4 Workspace context

When discovery includes uncommitted modifications, AEW must distinguish the working-tree observation from the committed repository baseline.

### 3.5 Subproject scope

A repository may contain multiple applications or components with different technologies.

For example:

```text
repository/
├── backend/
│   ├── pom.xml
│   └── src/
├── frontend/
│   ├── package.json
│   └── src/
└── infrastructure/
    └── terraform/
```

The profile must support scoped observations.

It must not incorrectly describe the entire repository as having one uniform build system.

---

## 4. Profile Dimensions

The initial profile model should support the following dimensions.

### 4.1 Programming languages

Identify languages supported by repository evidence.

Examples:

- COBOL.
- JCL.
- Java.
- Go.
- Python.
- PHP.
- C and C++.
- C#.
- JavaScript.
- TypeScript.
- SQL.
- Shell scripting.

Language detection should consider more than file extensions when ambiguity matters.

For example, generated source files or vendored dependencies may distort language distribution.

### 4.2 Frameworks and libraries

Identify relevant frameworks and major libraries.

Examples include:

- Spring Boot.
- Laravel.
- Symfony.
- ASP.NET Core.
- React.
- Express.
- FastAPI.

Framework identification must be supported by dependency manifests, configuration, imports, or other relevant evidence.

A language does not imply a framework.

### 4.3 Build systems

Identify actual build mechanisms.

Examples:

- Maven.
- Gradle.
- Go tooling.
- Composer.
- npm.
- Make.
- CMake.
- MSBuild.
- Custom scripts.
- Mainframe build and deployment processes.

AEW must distinguish a discovered build command from a command that has been successfully executed.

### 4.4 Dependency management

Identify dependency declarations and management mechanisms.

Examples:

- `pom.xml`.
- `build.gradle`.
- `go.mod`.
- `pyproject.toml`.
- `composer.json`.
- `package.json`.
- NuGet project files.
- Custom dependency definitions.

Dependency manifests provide evidence about declared dependencies.

They do not necessarily prove that every dependency is installed or available in the current environment.

### 4.5 Testing

Identify:

- Test frameworks.
- Test directories.
- Test naming conventions.
- Test execution commands.
- Integration test requirements.
- Test fixtures.
- CI test workflows.
- Known verification limitations.

AEW must distinguish:

- Discovered test commands.
- Recommended test commands.
- Previously executed test commands.
- Currently verified test results.

### 4.6 Code quality tooling

Identify:

- Formatters.
- Linters.
- Static analyzers.
- Type checkers.
- Security scanners.
- Repository quality gates.

Detected tooling should be associated with its actual configuration.

### 4.7 Repository organization

Identify meaningful repository regions, such as:

- Applications.
- Services.
- Shared libraries.
- Infrastructure.
- Tests.
- Documentation.
- Generated artifacts.
- Vendor directories.
- Deployment definitions.

### 4.8 Architectural characteristics

The profile may describe observed architectural patterns, including:

- Layered architecture.
- Modular monolith.
- Microservices.
- Hexagonal architecture.
- Event-driven components.
- Batch processing.
- Mainframe transaction processing.
- Legacy integration boundaries.

Architectural classifications must remain evidence-backed.

AEW must not infer an entire architectural style from a single directory name.

### 4.9 Runtime and deployment

Identify relevant runtime characteristics:

- Operating system assumptions.
- Container configuration.
- Runtime versions.
- Environment variables.
- Database dependencies.
- CI/CD pipelines.
- Deployment targets.
- External services.

Sensitive configuration values must not be copied into the profile.

### 4.10 Engineering conventions

Identify conventions such as:

- Naming.
- Directory organization.
- Error handling.
- Logging.
- Dependency injection.
- Testing patterns.
- Documentation style.
- API design.
- Database migration practices.
- Commit conventions.

Conventions may vary between repository regions.

---

## 5. Evidence and Provenance

Profile assertions must retain supporting evidence.

### 5.1 Evidence sources

Possible evidence includes:

- Source files.
- Dependency manifests.
- Build configuration.
- Test configuration.
- CI workflows.
- Documentation.
- Accepted project ADRs.
- Verified execution results.
- Explicit engineer-provided constraints.

### 5.2 Evidence hierarchy

AEW must distinguish the authority of different sources.

For example:

A repository's accepted ADR may establish an intended architectural constraint.

Source code may establish what is currently implemented.

A test result may establish observed behavior under specific conditions.

These sources may disagree.

AEW must preserve the disagreement rather than silently choose whichever source is most convenient.

### 5.3 Verification status

Each profile assertion should support a verification classification such as:

- Verified.
- Provisional.
- Conflicting.
- Unknown.
- Stale.

The exact persistence representation may be refined during implementation.

### 5.4 Provenance retention

A profile assertion must remain traceable to its supporting source or observation.

The Project Brain must not reduce evidence-backed claims to unexplained strings.

### 5.5 Human-provided information

Explicit engineer-provided constraints may carry authority appropriate to their source.

However, they must remain distinguishable from independently observed repository facts.

---

## 6. Discovery Strategy

AEW will use progressive discovery rather than requiring complete repository analysis before any useful work can begin.

ADR-007 defines staged discovery in greater detail.

### 6.1 Initial discovery

Initial discovery should identify high-value repository characteristics at low cost.

Examples:

- Repository structure.
- Common source languages.
- Dependency manifests.
- Build files.
- Test configuration.
- CI workflows.
- Existing documentation.

### 6.2 Targeted discovery

When a task concerns a particular component, AEW should investigate that region more deeply.

For example, a task involving authentication may require inspection of:

- Authentication services.
- Relevant configuration.
- Middleware.
- Authorization contracts.
- Associated tests.

It should not automatically require deep analysis of unrelated frontend components.

### 6.3 Deep discovery

Complex or risky tasks may require deeper investigation of:

- Data flow.
- Control flow.
- Architectural dependencies.
- Domain invariants.
- Security boundaries.
- Concurrency.
- Failure behavior.

### 6.4 Incremental maintenance

Previously discovered information should be reused when its applicability remains supported.

AEW should avoid repeatedly rediscovering unchanged repository characteristics.

### 6.5 Unknown characteristics

If a characteristic cannot be established, AEW must preserve the unknown state.

For example:

A repository containing Java files but no recognized build manifest must not automatically be classified as Maven-based.

---

## 7. Profile Structure

The Project Intelligence Profile is a logical model, not necessarily a single database record.

### 7.1 Conceptual representation

```text
Project Intelligence Profile
│
├── Identity
│   ├── Project
│   ├── Repository
│   └── Revision context
│
├── Technologies
│   ├── Languages
│   ├── Frameworks
│   └── Libraries
│
├── Tooling
│   ├── Build systems
│   ├── Package managers
│   ├── Test runners
│   └── Quality tools
│
├── Structure
│   ├── Applications
│   ├── Components
│   └── Repository regions
│
├── Architecture
│   ├── Patterns
│   ├── Dependencies
│   └── Constraints
│
├── Conventions
│   ├── Coding
│   ├── Testing
│   └── Documentation
│
└── Evidence
    ├── Sources
    ├── Verification
    ├── Freshness
    └── Coverage
```

### 7.2 Graph integration

Profile information should be represented using Project Brain entities, assertions, and evidence relationships where appropriate.

AEW should avoid maintaining a separate mutable profile representation that contradicts the graph's published snapshots.

### 7.3 Derived views

A compact profile document or JSON representation may be generated for AI consumption.

Such representations are derived views.

They must retain enough provenance and revision information to avoid presenting stale knowledge as current.

### 7.4 Partial profiles

A valid profile may be incomplete.

Coverage must be explicit.

AEW must not require every profile dimension to be populated before supporting a task.

---

## 8. Project-Specific Conventions

Repository conventions require particular care because they influence generated code.

### 8.1 Discovery before enforcement

AEW should discover existing conventions before recommending changes.

It must not automatically impose its own preferred formatting, architecture, or naming style.

### 8.2 Regional conventions

Different repository regions may follow different conventions.

For example:

```text
legacy/
    COBOL and JCL conventions

services/
    Java and Spring conventions

tools/
    Go conventions
```

AEW must preserve these distinctions.

### 8.3 Conflicting conventions

If documentation specifies one convention while existing code consistently follows another, AEW must report the discrepancy when relevant.

It must not silently declare either source authoritative without considering the applicable decision hierarchy.

### 8.4 Generated code

Generated source files should not automatically define preferred human-authored coding conventions.

### 8.5 Convention changes

A task requesting a convention change must be treated as a deliberate engineering change.

AEW must not perform broad formatting or structural rewrites merely because a new convention appears preferable.

---

## 9. Profile Freshness

Repository characteristics may change over time.

Examples include:

- Framework upgrades.
- Dependency changes.
- Build system migration.
- New test frameworks.
- Repository restructuring.
- Architectural refactoring.
- New deployment processes.

### 9.1 Revision applicability

Source-derived profile assertions must be associated with relevant repository revisions.

### 9.2 Targeted invalidation

When relevant files change, affected profile assertions may become stale.

For example:

A change to `pom.xml` may invalidate dependency or build configuration observations.

It does not necessarily invalidate unrelated domain model observations.

### 9.3 Revalidation

AEW should revalidate affected assertions when needed for a task.

### 9.4 No automatic freshness inheritance

An assertion verified at an earlier commit does not become current merely because it appears in a newly generated profile summary.

### 9.5 Profile history

Historical profile observations should remain reconstructable through ADR-003's snapshot model.

---

## 10. Context Package Integration

ADR-009 defines Context Packages.

The Project Intelligence Profile provides task-relevant project characteristics for those packages.

### 10.1 Relevant selection

A Context Package should include only profile information relevant to the task.

For example:

A Java bug fix may require:

- Java version.
- Relevant framework.
- Build command.
- Test runner.
- Coding conventions.
- Related architectural constraints.

It should not automatically include unrelated frontend tooling.

### 10.2 Provenance

Included profile assertions must retain their evidence and verification status.

### 10.3 Uncertainty

Unknown or provisional project characteristics must remain identifiable.

### 10.4 Revision binding

Profile information included in a Context Package must be consistent with the package's repository and Project Brain snapshot identity.

### 10.5 Context size

AEW should prefer compact, relevant profile views over exhaustive repository inventories.

---

## 11. Planning Integration

ADR-012 establishes adaptive planning.

Project intelligence influences planning complexity and verification selection.

### 11.1 Task assessment

The profile may help estimate:

- Scope.
- Architectural impact.
- Relevant dependencies.
- Testing complexity.
- Environment requirements.
- Migration risk.
- Uncertainty.

### 11.2 Planning profile

A well-understood localized change may qualify for Quick planning.

A change involving poorly understood legacy integration boundaries may require Standard, Deep, or Explore planning.

The planning profile must reflect actual evidence and risk.

It must not be determined solely by the programming language.

### 11.3 Work Unit boundaries

Project structure and architectural relationships may inform meaningful Work Unit decomposition.

### 11.4 Verification selection

The profile may suggest relevant verification commands.

However, discovered commands must not be represented as successfully executed tests.

---

## 12. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Project-specific discovery

AEW must discover repository characteristics rather than impose a universal technology profile.

### INV-002 — Evidence-backed assertions

Profile claims must retain identifiable supporting evidence.

### INV-003 — Revision applicability

Source-derived profile assertions must be associated with relevant repository observations.

### INV-004 — Partial knowledge support

Profiles may be incomplete without being invalid.

### INV-005 — Unknown remains unknown

Missing evidence must not be replaced with unsupported assumptions.

### INV-006 — Regional specificity

Different repository regions may have different technologies and conventions.

### INV-007 — Authority separation

Observed implementation, documented intent, and explicit engineering constraints must remain distinguishable.

### INV-008 — No implicit authorization

Profile information cannot authorize repository modifications or restricted operations.

### INV-009 — Incremental maintenance

Profile updates should reuse applicable knowledge and invalidate affected regions selectively.

### INV-010 — Context consistency

Profile information included in Context Packages must preserve revision and evidence consistency.

### INV-011 — Convention preservation

AEW must not silently impose unrelated coding conventions on a repository.

### INV-012 — Technology independence

The Project Intelligence Profile must support heterogeneous and mixed-language repositories.

### INV-013 — No false verification

Discovered build and test commands must not be presented as verified successful executions.

---

## 13. Alternatives Considered

The following alternatives summarize the architectural tradeoffs relevant to the accepted decision.

### 13.1 Universal project template

**Advantages**

- Simple implementation.
- Predictable initial structure.
- Easy integration with fixed tooling.

**Disadvantages**

- Poor fit for heterogeneous repositories.
- Incorrect assumptions about frameworks.
- Weak support for legacy systems.
- Encourages unnecessary architectural conformity.

**Disposition:** Rejected as the primary intelligence model.

### 13.2 Language-only classification

**Advantages**

- Fast discovery.
- Simple file-extension analysis.

**Disadvantages**

- Does not identify frameworks or build systems reliably.
- Misses regional differences.
- Provides insufficient verification guidance.
- Cannot capture architectural constraints.

**Disposition:** Insufficient.

### 13.3 Full repository analysis before task execution

**Advantages**

- Potentially broad initial knowledge.
- Fewer unknown regions after successful analysis.

**Disadvantages**

- High initial cost.
- Delays useful work.
- Repeated analysis may be unnecessary.
- Difficult to maintain on large repositories.

**Disposition:** Rejected as a universal prerequisite.

### 13.4 AI-generated profile without evidence

**Advantages**

- Fast to produce.
- Flexible narrative representation.

**Disadvantages**

- Difficult to verify.
- May contain hallucinated conventions.
- Poor revision tracking.
- Weak support for incremental invalidation.

**Disposition:** Rejected as the authoritative profile representation.

### 13.5 Hardcoded framework-specific adapters

**Advantages**

- Potentially precise for supported frameworks.
- Straightforward specialized detection.

**Disadvantages**

- Poor portability.
- Expensive maintenance.
- Encourages premature framework proliferation.

**Disposition:** Specialized detectors may be added when justified, but the core profile remains framework-independent.

---

## 14. Consequences

### 14.1 Positive consequences

- Better adaptation to real repositories.
- Reduced repeated investigation.
- More relevant context selection.
- Improved verification recommendations.
- Support for mixed-language projects.
- Better preservation of existing conventions.
- More accurate planning.
- Incremental knowledge maintenance.
- Improved legacy modernization support.

### 14.2 Costs

- Discovery logic must be maintained.
- Evidence references require persistence.
- Profile assertions may conflict.
- Regional classifications add complexity.
- Freshness tracking requires targeted invalidation.
- Some characteristics may remain unknown.

### 14.3 Risks

**False framework detection**

A dependency or directory name may be misinterpreted.

Mitigation: Require sufficient evidence and preserve provisional status.

**Stale conventions**

Repository conventions may change after discovery.

Mitigation: Revision-aware assertions and targeted invalidation.

**Overgeneralization**

A convention observed in one module may be applied to the entire repository.

Mitigation: Scoped profile assertions.

**Excessive discovery**

The system may spend too much time investigating unrelated components.

Mitigation: Staged discovery and task-relevant depth.

**Conflicting evidence**

Documentation and implementation may disagree.

Mitigation: Preserve provenance and report conflicts.

---

## 15. Implementation Guidance

### 15.1 Initial implementation milestone

The Project Intelligence Profile should be introduced during M2.

### 15.2 Minimum viable discovery

The initial implementation should support:

- Repository language detection.
- Dependency manifest discovery.
- Build system identification.
- Test configuration discovery.
- CI workflow discovery.
- Repository region identification.
- Basic convention extraction.
- Evidence references.
- Revision applicability.

Advanced architectural inference may be added incrementally.

### 15.3 Suggested logical interfaces

Possible operations include:

```text
discover_project_profile(repository, revision)

discover_region_profile(repository, region, revision)

retrieve_profile(project, snapshot, scope)

invalidate_profile_region(project, changed_paths)

verify_profile_assertion(assertion, evidence)
```

These are conceptual operations, not mandated function signatures.

### 15.4 Detection strategy

Prefer deterministic detection for characteristics that can be established reliably from structured files.

Examples include dependency manifests and build configuration.

AI reasoning may assist with architectural interpretation and convention discovery.

However, inferred conclusions must retain evidence and uncertainty.

### 15.5 Storage integration

Profile assertions should use the Project Brain's immutable assertion and snapshot model.

Avoid introducing an unrelated mutable profile database.

### 15.6 Scope control

Discovery must respect repository boundaries and applicable access policies.

Files outside the authorized investigation scope must not be read merely to complete a profile.

### 15.7 Sensitive information

The profile may record the existence of environment variables or configuration dependencies.

It must not unnecessarily persist credentials, tokens, secrets, or sensitive configuration values.

### 15.8 Initial performance expectations

The first profile should be useful without requiring exhaustive source analysis.

Discovery should prioritize high-value configuration and structural evidence.

---

## 16. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Java repository using Maven | Maven detected from evidence |
| Java repository using Gradle | Gradle detected without assuming Maven |
| Java files without build manifest | Build system remains unknown |
| PHP repository without Laravel | Laravel is not inferred |
| Mixed Java and TypeScript repository | Both technologies represented with scoped evidence |
| COBOL and JCL repository | Legacy languages and build characteristics represented without forcing modern framework assumptions |
| Monorepo with separate applications | Regional profiles remain distinct |
| Generated source directory | Generated code does not automatically define conventions |
| Conflicting documentation and source | Conflict preserved |
| Missing test configuration | Test framework remains unknown |
| Discovered test command | Not marked as executed |
| Framework version changes | Affected assertions become stale |
| Unrelated file changes | Unaffected profile assertions may remain applicable |
| Historical profile retrieval | Original snapshot observations remain reproducible |
| Context Package generation | Relevant profile subset is included with provenance |
| Unknown technology | No unsupported default substituted |

### 16.1 Test isolation

Tests should use disposable repository fixtures.

No live production repository should be required for ordinary profile validation tests.

### 16.2 Deterministic and inferred findings

Tests must distinguish deterministic detections from AI-assisted interpretations.

The latter require explicit evidence and uncertainty handling.

### 16.3 Coverage

A test should not claim complete profile coverage merely because one technology was successfully detected.

Coverage must be assessed independently.

---

## 17. Related Decisions and Contracts

### Related ADRs

**ADR-001 — Hybrid Knowledge Storage Strategy**

Establishes the SQLite Project Brain.

**ADR-003 — Revision-Scoped Graph Snapshots**

Provides immutable, revision-aware profile assertion storage.

**ADR-007 — Staged Discovery and Targeted Invalidation**

Defines incremental discovery and maintenance.

**ADR-008 — Progressive Knowledge Depth**

Defines investigation depth independently of freshness.

**ADR-009 — Immutable Context Packages**

Defines how task-relevant profile knowledge is packaged.

**ADR-012 — Adaptive Planning**

Uses project characteristics to guide planning and verification.

### Related contracts

- `contracts/context.schema.json`
- `contracts/task.schema.json`

Additional internal Project Intelligence Profile contracts may be introduced during M2.

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 18. Open Implementation Questions

The accepted architecture does not yet prescribe:

1. The exact persistence schema for profile assertions.
2. The initial language and framework detector catalog.
3. The method for measuring profile coverage.
4. The strategy for detecting conventions from representative source samples.
5. The method for resolving conflicting evidence.
6. The mechanism for recognizing generated or vendored code.
7. The policy for revalidating framework versions.
8. The format of compact profile views supplied to AI skills.
9. The threshold for introducing specialized technology detectors.
10. The performance budget for initial discovery.

These decisions should be made during implementation using actual repository requirements and verification evidence.

They must preserve the invariants defined by this ADR.

---

## 19. Acceptance and Compliance

ADR-006 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Repository characteristics are discovered from evidence.
- Frameworks and build systems are not assumed from language alone.
- Mixed-language and multi-application repositories are supported.
- Regional conventions remain distinguishable.
- Profile assertions retain provenance and revision applicability.
- Unknown characteristics remain unknown.
- Profile information is incrementally maintained.
- Context Packages receive relevant, coherent profile information.
- Planning uses profile evidence without treating it as authorization.

Compliance requires observed verification results.

The existence of this ADR does not establish that the implementation already satisfies these requirements.

---

## 20. Decision Summary

AEW maintains an evidence-backed Project Intelligence Profile for each project.

The profile describes observed technologies, tooling, repository structure, architectural characteristics, and engineering conventions.

Profile assertions are revision-aware, scoped, and incrementally maintained within the Project Brain.

The system must support heterogeneous repositories and preserve uncertainty when evidence is incomplete.

Project Intelligence Profiles inform investigation, context selection, planning, implementation guidance, and verification.

They do not replace source evidence, architectural authority, or execution authorization.

**AEW must understand the repository that exists, not the repository an AI assistant assumes should exist.**