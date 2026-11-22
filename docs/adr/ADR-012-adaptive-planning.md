# ADR-012 — Adaptive Planning and Event-Driven Approval

**Status:** Accepted  
**Document version:** 0.1.0  
**Architecture baseline:** AEW v0.1  
**Decision scope:** Task assessment, adaptive planning, plan revisions, Work Unit decomposition, uncertainty management, and event-driven approval  
**Related milestones:** M4 — Adaptive Planning and Work Units; M5 — Controlled Execution; M7 — Integrated Skill-Driven Workflows

---

## 1. Context

The Adaptive Engineering Workbench (AEW) supports a wide range of engineering activities.

These include:

- Localized bug fixes.
- Small feature additions.
- Refactoring.
- Repository investigation.
- Architectural analysis.
- Legacy modernization.
- Multi-component implementation.
- Security-sensitive changes.
- Greenfield project development.
- Long-running engineering tasks.

These activities differ substantially in complexity, uncertainty, risk, and verification requirements.

A fixed planning workflow would create two undesirable outcomes.

First, simple tasks would become unnecessarily expensive.

A one-function bug fix might require extensive documentation, formal decomposition, multiple approvals, and detailed architectural analysis despite having a small and well-understood scope.

Second, complex tasks might receive insufficient analysis if the workflow were optimized exclusively for speed.

A change involving database consistency, concurrent execution, public interfaces, or security boundaries may require deeper investigation and explicit architectural review.

AEW therefore needs planning behavior that adapts to the actual engineering problem.

The system must also accommodate discoveries made during implementation.

A task initially believed to be simple may reveal unexpected dependencies, scope changes, or risks.

Planning must be revisable without allowing those revisions to silently expand execution authority.

---

## 2. Decision

AEW will use **adaptive planning profiles with versioned plans and event-driven approval checkpoints**.

The supported planning profiles are:

1. Quick.
2. Standard.
3. Deep.
4. Explore.

The selected profile determines the expected level of planning detail, investigation, decomposition, and review.

Planning depth must be proportional to task risk, uncertainty, scope, and architectural impact.

Approvals must be associated with meaningful decisions and restricted operations rather than every routine reasoning or tool step.

### 2.1 Core requirements

AEW must:

- Assess task characteristics before selecting a planning profile.
- Support escalation when new evidence changes the risk assessment.
- Avoid mandatory heavyweight planning for simple tasks.
- Preserve explicit plan revisions.
- Associate Work Units with the applicable plan revision.
- Bind authorization to the relevant approved scope.
- Reassess approval when material changes occur.
- Support read-only exploration without requiring implementation.
- Preserve uncertainty and unresolved decisions.
- Maintain human authority over restricted operations.

### 2.2 Fundamental separation

Planning determines what AEW proposes to accomplish.

Authorization determines what AEW may execute.

Execution determines what actually happens.

Verification establishes what was observed.

Delivery communicates the resulting engineering outcome.

These responsibilities must remain distinct.

---

## 3. Planning Profiles

### 3.1 Overview

| Profile | Intended use | Planning emphasis |
|---|---|---|
| Quick | Small, localized, low-risk tasks | Minimal sufficient planning |
| Standard | Ordinary engineering changes | Scope, dependencies, verification |
| Deep | High-risk or cross-cutting work | Architecture, invariants, migration, risk |
| Explore | Investigation without implementation commitment | Evidence, hypotheses, uncertainty |

Profiles describe planning behavior.

They do not independently grant execution authority.

---

## 4. Quick Planning

### 4.1 Purpose

Quick planning supports well-understood, localized engineering tasks.

Examples include:

- Correcting a simple conditional.
- Fixing a localized null-handling defect.
- Updating a small configuration value.
- Adding a focused regression test.
- Correcting documentation.
- Making a narrowly scoped compatibility adjustment.

### 4.2 Expected characteristics

Quick tasks generally have:

- Limited change scope.
- Low architectural impact.
- Low uncertainty.
- Known implementation boundaries.
- Available verification.
- Minimal dependency complexity.

### 4.3 Minimum plan

A Quick plan should identify:

1. Objective.
2. Intended scope.
3. Expected change.
4. Verification.
5. Known risks or assumptions.

### 4.4 Work Units

A Quick task will often contain one Work Unit.

Multiple Work Units are permitted when justified.

### 4.5 Documentation overhead

Quick planning should not require a lengthy specification or architectural document.

A concise structured plan is sufficient.

### 4.6 Escalation

A Quick task must escalate when new evidence reveals material complexity or risk.

For example:

```text
Initial task:
    Fix a null response.

Discovery:
    Null behavior is part of a shared API contract.

New concern:
    Multiple consumers rely on the existing behavior.

Action:
    Reassess planning profile and affected scope.
```

The system must not continue under the original low-risk assumptions without reassessment.

---

## 5. Standard Planning

### 5.1 Purpose

Standard planning supports ordinary engineering work involving several implementation considerations.

Examples include:

- Adding an API endpoint.
- Implementing a service.
- Updating a database access layer.
- Introducing a small integration.
- Refactoring a bounded subsystem.
- Adding a feature across several related files.

### 5.2 Expected characteristics

Standard tasks may involve:

- Multiple files or components.
- Known dependencies.
- Moderate uncertainty.
- Existing architectural conventions.
- Several verification requirements.
- Limited compatibility considerations.

### 5.3 Expected plan

A Standard plan should identify:

- Objective.
- Scope and exclusions.
- Relevant Context Package.
- Affected components.
- Dependencies.
- Work Units.
- Acceptance criteria.
- Verification strategy.
- Risks and uncertainties.
- Required approval events.

### 5.4 Work Units

Standard planning should use meaningful Work Units when the task contains separable engineering outcomes.

### 5.5 Verification

Verification should reflect the actual project tooling and affected behavior.

The Project Intelligence Profile may inform test selection.

### 5.6 Review

Review checkpoints should occur at meaningful boundaries rather than after every implementation step.

---

## 6. Deep Planning

### 6.1 Purpose

Deep planning supports complex, high-risk, or architecturally significant engineering work.

Examples include:

- Replacing a persistence subsystem.
- Introducing a new execution model.
- Migrating legacy integrations.
- Changing public contracts.
- Modifying authentication or authorization.
- Redesigning transactional behavior.
- Performing a substantial data migration.
- Implementing concurrency-sensitive infrastructure.
- Introducing cross-service architectural changes.

### 6.2 Expected characteristics

Deep tasks may involve:

- Multiple architectural boundaries.
- High uncertainty.
- Significant dependencies.
- Compatibility risks.
- Security implications.
- Data integrity concerns.
- Complex verification.
- Long-running implementation.
- Difficult rollback or recovery.

### 6.3 Expected plan

A Deep plan should address:

1. Problem definition.
2. Current-state evidence.
3. Desired outcomes.
4. Scope and exclusions.
5. Architectural constraints.
6. Relevant invariants.
7. Alternatives and tradeoffs.
8. Dependency analysis.
9. Work Unit decomposition.
10. Verification strategy.
11. Compatibility and migration.
12. Failure and recovery considerations.
13. Risks and uncertainties.
14. Required decisions and approvals.
15. Delivery strategy.

### 6.4 Architectural decisions

Deep planning may identify a need for a new ADR.

However, not every Deep task requires one.

An ADR is appropriate when the task establishes or changes a significant architectural decision.

### 6.5 Incremental implementation

Deep planning should favor coherent, verifiable implementation increments.

The existence of a comprehensive plan does not require executing the entire plan in one uninterrupted session.

### 6.6 Review checkpoints

Deep tasks should identify meaningful checkpoints for architectural decisions, contract changes, and implementation milestones.

---

## 7. Explore Planning

### 7.1 Purpose

Explore supports investigation when the correct implementation is not yet established.

Examples include:

- Understanding unfamiliar repository behavior.
- Investigating a difficult defect.
- Evaluating architectural alternatives.
- Characterizing a legacy subsystem.
- Analyzing performance problems.
- Investigating concurrency risks.
- Assessing modernization feasibility.
- Determining whether a proposed change is necessary.

### 7.2 Expected characteristics

Explore tasks may have:

- High uncertainty.
- Unclear implementation scope.
- Multiple hypotheses.
- Incomplete evidence.
- Unknown dependencies.
- No immediate implementation commitment.

### 7.3 Expected plan

An Explore plan should identify:

- Investigation objective.
- Known evidence.
- Hypotheses or questions.
- Relevant repository regions.
- Investigation approach.
- Expected findings.
- Stopping criteria.
- Resource budget.
- Unresolved uncertainties.

### 7.4 Read-only default

Explore should be read-only by default.

Investigation does not imply authorization to modify repository files.

### 7.5 Deliverables

Explore may produce:

- Findings.
- Evidence references.
- Architectural observations.
- Reproduction steps.
- Risk analysis.
- Recommended next actions.
- Proposed implementation scope.
- A recommendation to continue investigating.

### 7.6 No artificial commit requirement

A read-only Explore task does not require a proposed Git commit.

The Execution Contract must support this behavior.

### 7.7 Transition to implementation

Explore may lead to a Quick, Standard, or Deep implementation plan.

That transition requires an explicit planning decision and applicable authorization.

Exploration findings do not automatically authorize implementation.

---

## 8. Planning Profile Selection

AEW should assess task characteristics before selecting a profile.

### 8.1 Assessment dimensions

The initial assessment should consider:

- Scope.
- Complexity.
- Uncertainty.
- Architectural impact.
- Security sensitivity.
- Data integrity impact.
- Concurrency risk.
- Dependency breadth.
- Reversibility.
- Verification difficulty.
- Existing knowledge depth.
- Knowledge freshness.
- Availability of acceptance criteria.

### 8.2 Evidence sources

Assessment may use:

- Task description.
- Repository preflight.
- Project Intelligence Profile.
- Project Brain assertions.
- Context Package.
- Existing tests.
- Relevant ADRs.
- Active PR coordination.
- Explicit engineer constraints.

### 8.3 No rigid score requirement

The architecture does not require a single numerical complexity score.

A scoring model may be introduced if useful, but it must remain interpretable and evidence-backed.

### 8.4 Risk-sensitive selection

A small change may still require Deep planning if it affects a critical invariant.

For example, a one-line modification to authorization logic may carry greater risk than a multi-file documentation update.

File count is not a reliable substitute for risk assessment.

### 8.5 Human override

The engineer may request a different planning profile.

However, a requested lighter profile must not bypass mandatory security, authorization, or consistency controls.

### 8.6 Unknown characteristics

When material risk or scope cannot be established, AEW should preserve the uncertainty and consider Explore or additional discovery.

Unknown risk must not automatically be classified as low risk.

---

## 9. Planning Profile Transitions

Planning profiles may change during a task.

### 9.1 Escalation

Escalation may occur when:

- Unexpected dependencies are discovered.
- Scope expands materially.
- A public contract is affected.
- A security boundary is involved.
- Verification becomes more complex.
- Existing assumptions are invalidated.
- Knowledge coverage is insufficient.

### 9.2 De-escalation

A task may move to a lighter profile when investigation resolves uncertainty and demonstrates a smaller scope.

### 9.3 Explicit transitions

Material profile transitions must be recorded in the plan history.

### 9.4 Authorization impact

A profile change does not automatically invalidate every existing approval.

However, changes to approved operations, scope, baseline, or other grant-bound conditions require authorization reassessment.

### 9.5 No silent continuation

AEW must not continue executing against assumptions known to be materially invalid.

---

## 10. Plan Identity and Revisioning

Plans must have stable identities and explicit revisions.

### 10.1 Plan identity

A plan identifies the engineering approach associated with a task.

### 10.2 Plan revision

Each material plan change must produce a distinguishable revision.

### 10.3 Revision contents

A plan revision should identify:

- Plan identity.
- Revision identity.
- Task identity.
- Planning profile.
- Context Package.
- Objective.
- Scope.
- Work Units.
- Dependencies.
- Acceptance criteria.
- Verification requirements.
- Risks and uncertainties.
- Required approvals.

### 10.4 Historical preservation

Previous plan revisions must remain traceable.

AEW must not silently overwrite the plan revision used by an earlier execution.

### 10.5 Revision relationships

A revised plan should identify its predecessor and relevant changes.

### 10.6 No implicit authorization inheritance

A new plan revision must not automatically inherit permissions that no longer apply.

### 10.7 Nonmaterial edits

Editorial clarifications that do not alter execution meaning may be handled according to the plan's versioning policy.

The implementation must define which changes require a new material revision.

---

## 11. Material Change Detection

AEW must identify changes that affect the approved engineering boundary.

### 11.1 Material changes

Examples include:

- New files outside approved scope.
- New protected-path interactions.
- New external effects.
- Changed repository baseline.
- Changed Context Package applicability.
- New required Git operations.
- Modified Work Unit objectives.
- Changed security assumptions.
- Changed architectural contracts.
- Expanded resource requirements.

### 11.2 Nonmaterial changes

Examples may include:

- Clarifying an implementation note.
- Reordering internal steps without changing scope.
- Updating explanatory wording.
- Correcting a typographical error.

### 11.3 Context-sensitive assessment

Materiality depends on the active authorization and task.

A file addition within an approved directory may be permitted by one grant but not another.

### 11.4 Deterministic enforcement

The execution controller must enforce actual grant boundaries regardless of the AI's materiality assessment.

### 11.5 Uncertain materiality

When AEW cannot determine whether a change remains authorized, it must not assume that the original grant covers it.

---

## 12. Event-Driven Approval

AEW will use approval checkpoints associated with meaningful engineering events.

### 12.1 Purpose

Event-driven approval provides human control without requiring approval after every routine operation.

### 12.2 Approval events

Approval may be required when:

- Beginning a restricted implementation.
- Creating a task branch.
- Expanding approved file scope.
- Changing a material plan assumption.
- Crossing an architectural boundary.
- Performing a destructive operation.
- Extending execution budgets.
- Resuming after authorization invalidation.
- Staging changes.
- Creating a commit.
- Pushing changes.
- Creating a pull request.
- Merging changes.

### 12.3 Scoped approvals

A trusted Approval Grant may authorize a bounded set of operations.

The engine should not repeatedly request approval for operations already covered by a valid grant.

### 12.4 No blanket autonomy

A grant must not become unrestricted permission for all future work.

### 12.5 Approval expiration and revocation

Authorization must remain subject to applicable expiration, revocation, and state-binding rules.

### 12.6 Review versus authorization

Human review of an implementation result is not automatically equivalent to authorization for Git publication.

The system must preserve this distinction.

### 12.7 Trusted issuance

Approval must originate from a trusted mechanism as defined by ADR-010.

An AI-generated approval document does not establish authority.

---

## 13. Planning and Context Packages

ADR-009 defines immutable Context Packages.

Plans must be grounded in explicit context.

### 13.1 Context binding

A plan revision should identify the Context Package supporting its assumptions.

### 13.2 Context expansion

Additional investigation may produce a new Context Package.

### 13.3 Plan reassessment

When a new package materially changes the understanding of scope, dependencies, or risk, AEW must reassess the plan.

### 13.4 Revision compatibility

A plan must not silently combine incompatible repository observations.

### 13.5 Uncertainty

Unresolved context questions must remain visible in planning.

### 13.6 No implicit authority

A Context Package cannot authorize the plan's execution.

---

## 14. Planning and Work Units

ADR-011 defines adaptive Work Units.

### 14.1 Decomposition

Planning may divide a task into meaningful Work Units.

### 14.2 Proportionality

A Quick task may require one unit.

A Deep task may require several.

### 14.3 Dependency tracking

Work Unit dependencies must be explicit when they affect execution order.

### 14.4 Verification boundaries

Each implementation Work Unit should have proportionate acceptance and verification criteria.

### 14.5 Review checkpoints

Planning should identify meaningful review points.

### 14.6 Plan revisions

Material changes to Work Unit boundaries must be reflected in the plan.

### 14.7 Delivery

Work Units normally produce one proposed commit per meaningful implementation unit.

Read-only investigation does not require an artificial commit.

---

## 15. Planning and Repository Preflight

ADR-005 establishes mandatory Git preflight.

### 15.1 Preflight evidence

Planning should consider:

- Repository identity.
- Integration baseline.
- Workspace state.
- Branch collisions.
- Active PRs.
- Known coordination risks.
- Missing remote evidence.

### 15.2 Incomplete preflight

Missing mandatory preflight evidence must not be interpreted as clearance for implementation.

### 15.3 Planning may continue

Read-only planning and investigation may continue while some preflight information remains unavailable, subject to applicable policy.

### 15.4 Implementation gate

Restricted implementation must satisfy the relevant preflight and authorization requirements.

### 15.5 Freshness

Preflight observations must be revalidated when their assumptions may have changed.

---

## 16. Planning Budgets

Planning itself may consume substantial resources.

### 16.1 Purpose

Budgets prevent excessive analysis and repeated investigation without meaningful progress.

### 16.2 Possible dimensions

Planning budgets may include:

- Investigation time.
- Tool calls.
- Context expansion.
- Repository regions analyzed.
- Reasoning iterations.
- External requests.

### 16.3 Proportionality

Quick tasks should generally require less planning effort than Deep investigations.

### 16.4 Progress awareness

Budget decisions should consider whether additional investigation is reducing meaningful uncertainty.

### 16.5 Hard boundaries

Progress-aware budgeting must not eliminate applicable hard limits.

### 16.6 Exhaustion

When a planning budget is exhausted, AEW must report the current findings and unresolved questions.

It must not fabricate completion.

### 16.7 Extension

Budget extensions must follow applicable authorization rules.

---

## 17. Planning Outputs

Each planning profile should produce an artifact proportionate to its purpose.

### 17.1 Quick output

A concise plan containing:

- Objective.
- Scope.
- Intended change.
- Verification.
- Known risks.

### 17.2 Standard output

A structured plan containing:

- Objective.
- Scope.
- Dependencies.
- Work Units.
- Acceptance criteria.
- Verification.
- Risks.
- Required approvals.

### 17.3 Deep output

A detailed plan containing:

- Current-state analysis.
- Architectural constraints.
- Alternatives.
- Invariants.
- Dependencies.
- Work Units.
- Migration considerations.
- Verification strategy.
- Recovery considerations.
- Risks.
- Approval checkpoints.

### 17.4 Explore output

An investigation plan and findings record containing:

- Questions.
- Hypotheses.
- Evidence.
- Observations.
- Uncertainty.
- Recommended next actions.

### 17.5 Common requirements

Regardless of profile, planning must preserve:

- Task identity.
- Relevant repository context.
- Scope.
- Uncertainty.
- Verification expectations.
- Applicable authorization boundaries.

---

## 18. Architectural Invariants

The following invariants are mandatory.

### INV-001 — Adaptive planning

AEW supports Quick, Standard, Deep, and Explore profiles.

### INV-002 — Proportionality

Planning effort must reflect actual task risk, uncertainty, scope, and complexity.

### INV-003 — No mandatory heavyweight workflow

Simple tasks must not require unnecessary architectural ceremonies.

### INV-004 — Risk-sensitive escalation

Materially increased risk or scope requires planning reassessment.

### INV-005 — Explicit plan revisions

Material plan changes must produce traceable revisions.

### INV-006 — Historical traceability

Earlier plan revisions must remain identifiable.

### INV-007 — Context binding

Plans must retain the Context Package supporting their assumptions.

### INV-008 — Work Unit coherence

Implementation plans must use meaningful Work Unit boundaries where decomposition is appropriate.

### INV-009 — Event-driven approval

Approval checkpoints must correspond to meaningful decisions or restricted operations.

### INV-010 — No implicit authority

Planning does not independently authorize execution.

### INV-011 — Scoped approval

Existing trusted grants may authorize bounded operations without repetitive approval.

### INV-012 — Material change reassessment

Material changes must be evaluated against active authorization.

### INV-013 — Explore without implementation

Read-only investigation must not require implementation or commit preparation.

### INV-014 — Explicit uncertainty

Unresolved questions and incomplete evidence must remain visible.

### INV-015 — Budget honesty

Planning must not claim completion when required investigation remains unfinished.

### INV-016 — No authorization inheritance by assumption

New plan revisions cannot silently inherit authority beyond the original grant's applicable scope.

---

## 19. Alternatives Considered

The following alternatives summarize the tradeoffs relevant to the accepted architecture.

### 19.1 One planning process for every task

**Advantages**

- Predictable workflow.
- Uniform documentation.

**Disadvantages**

- Excessive overhead for small tasks.
- Poor proportionality.
- Slower engineering work.

**Disposition:** Rejected.

### 19.2 No explicit planning

**Advantages**

- Minimal initial latency.
- High flexibility.

**Disadvantages**

- Weak scope control.
- Poor traceability.
- Difficult authorization.
- Higher risk of uncontrolled changes.

**Disposition:** Rejected as the general model.

### 19.3 Always use Deep planning

**Advantages**

- Thorough analysis.
- Explicit architectural considerations.

**Disadvantages**

- Expensive.
- Slow.
- Unnecessary for localized changes.
- Encourages speculative design.

**Disposition:** Rejected.

### 19.4 Fixed numerical complexity thresholds

**Advantages**

- Easy automation.
- Deterministic classification.

**Disadvantages**

- Difficult to represent contextual risk.
- May classify security-sensitive small changes incorrectly.
- Encourages artificial scoring.

**Disposition:** Not required by the architecture.

### 19.5 Approval after every tool invocation

**Advantages**

- Frequent human intervention.

**Disadvantages**

- Approval fatigue.
- Excessive interruptions.
- Poor usability.

**Disposition:** Rejected as the default.

### 19.6 One approval for the entire project

**Advantages**

- Minimal interruptions.

**Disadvantages**

- Excessive authority.
- Weak scope boundaries.
- Poor revocation and revision handling.

**Disposition:** Rejected.

### 19.7 Mutable plans without revision history

**Advantages**

- Simple editing.

**Disadvantages**

- Difficult to reconstruct earlier decisions.
- Authorization bindings become ambiguous.
- Execution history loses context.

**Disposition:** Rejected.

---

## 20. Consequences

### 20.1 Positive consequences

- Lower overhead for small tasks.
- More rigorous treatment of high-risk work.
- Better alignment between planning and engineering complexity.
- Improved traceability.
- Safer scope changes.
- Reduced approval fatigue.
- Better human control.
- More efficient repository investigation.
- Support for read-only exploration.
- Improved long-running task management.

### 20.2 Costs

- Task assessment logic.
- Multiple planning representations.
- Plan revision management.
- Material change detection.
- Approval event tracking.
- Work Unit integration.
- Context consistency checks.
- Additional semantic validation.

### 20.3 Risks

**Under-planning**

A task may be classified as Quick despite hidden complexity.

Mitigation: Preserve uncertainty and support escalation.

**Over-planning**

A simple task may be classified as Deep unnecessarily.

Mitigation: Use proportionality and evidence-backed assessment.

**Plan drift**

Implementation may diverge from the approved plan.

Mitigation: Scope validation and material change detection.

**Approval fatigue**

Too many approval events may interrupt work.

Mitigation: Scoped grants and meaningful checkpoints.

**Authority confusion**

An AI-generated plan may be treated as approved execution.

Mitigation: Trusted authorization enforcement.

**Stale context**

A plan may rely on outdated repository knowledge.

Mitigation: Context Package binding and applicability revalidation.

---

## 21. Implementation Guidance

### 21.1 Initial milestone

Adaptive planning should be implemented during M4.

Controlled execution integration belongs to M5.

Integrated skill workflows belong to M7.

### 21.2 Minimum viable planning engine

The initial implementation should support:

- Task assessment.
- Planning profile selection.
- Plan identity.
- Plan revision.
- Context Package binding.
- Scope and exclusions.
- Work Unit decomposition.
- Dependencies.
- Acceptance criteria.
- Verification requirements.
- Risks and uncertainties.
- Approval event identification.

### 21.3 Suggested logical interfaces

Possible operations include:

```text
assess_task(task, context)

select_planning_profile(assessment)

create_plan(task, context, profile)

decompose_plan_into_work_units(plan)

evaluate_plan_change(previous, proposed)

identify_required_approval_events(plan)

validate_plan_revision(plan, context)

prepare_plan_for_execution(plan, grant)
```

These are conceptual operations, not mandated function signatures.

### 21.4 AI and deterministic responsibilities

AI reasoning may assist with:

- Task interpretation.
- Risk identification.
- Architectural analysis.
- Work Unit proposals.
- Verification recommendations.
- Plan revision suggestions.

Deterministic code must enforce:

- Contract validity.
- Stable identities.
- Revision consistency.
- Grant scope.
- Protected operations.
- Execution boundaries.

### 21.5 Materiality assessment

The AI may propose whether a change is material.

The execution controller must independently enforce the actual authorization constraints.

### 21.6 Avoid premature complexity

The initial implementation does not require:

- A general-purpose workflow engine.
- Complex numerical risk scoring.
- Organization-wide approval dashboards.
- Automated project management synchronization.
- Distributed planning orchestration.
- Autonomous architectural decision acceptance.

These capabilities may be considered later when justified.

---

## 22. Verification

The following tests should demonstrate compliance.

| Scenario | Expected result |
|---|---|
| Localized low-risk bug fix | Quick planning supported |
| Ordinary multi-file feature | Standard planning supported |
| Security-sensitive change | Deep planning or justified equivalent safeguards |
| Unfamiliar repository behavior | Explore planning supported |
| Explore without modifications | No commit proposal required |
| New dependency discovered | Plan reassessment supported |
| Scope expands outside grant | Authorization reassessment required |
| Nonmaterial wording correction | No unnecessary execution invalidation |
| Material plan revision | New revision recorded |
| Historical plan queried | Earlier revision preserved |
| Context Package changes | Applicability reassessed |
| Approved Work Unit remains in scope | No unnecessary repeated approval |
| Protected operation requested | Trusted authorization required |
| Approval expired | Restricted operation denied |
| Plan revision differs from grant | Execution denied or reconciled |
| Planning budget exhausted | Unresolved questions reported |
| Quick task becomes complex | Escalation supported |
| Deep investigation reduces uncertainty | De-escalation supported where appropriate |
| Tests unavailable | Verification limitations preserved |
| Git preflight incomplete | No false implementation clearance |
| AI-generated approval claim | No authority granted |
| Plan accepted for review | No implicit Git publication |

### 22.1 Test isolation

Tests should use controlled task fixtures, isolated Project Brain state, and disposable repositories.

### 22.2 Deterministic testing

Contract and authorization behavior must be tested deterministically.

### 22.3 AI-assisted assessment testing

Where AI reasoning influences planning recommendations, evaluation should examine:

- Relevance.
- Risk recognition.
- Scope accuracy.
- Uncertainty reporting.
- Work Unit coherence.

AI recommendations must not be treated as deterministic authorization decisions.

### 22.4 Evidence

Compliance claims require observed test results.

The existence of planning logic does not establish that its recommendations are reliable.

---

## 23. Related Decisions and Contracts

### Related ADRs

**ADR-003 — Revision-Scoped Graph Snapshots**

Establishes coherent historical knowledge.

**ADR-004 — Workspace Consistency**

Defines repository modification safety.

**ADR-005 — Git Preflight**

Establishes repository readiness and coordination evidence.

**ADR-006 — Per-Project Intelligence Profiles**

Provides evidence-backed project characteristics.

**ADR-007 — Staged Discovery and Targeted Invalidation**

Defines proportional investigation and knowledge maintenance.

**ADR-008 — Progressive Knowledge Depth**

Defines investigation depth and freshness.

**ADR-009 — Immutable Context Packages**

Defines the knowledge boundary supporting plans.

**ADR-010 — Controlled Execution**

Defines trusted authorization and deterministic enforcement.

**ADR-011 — Adaptive Work Units and Delivery**

Defines meaningful implementation boundaries and delivery preparation.

### Related contracts

- `contracts/task.schema.json`
- `contracts/context.schema.json`
- `contracts/approval.schema.json`
- `contracts/execution.schema.json`
- `contracts/delivery.schema.json`

### Related documentation

- `docs/architecture.md`
- `docs/implementation-roadmap.md`
- `docs/codex-handoff.md`
- `docs/adr/README.md`
- `AGENTS.md`

---

## 24. Open Implementation Questions

The accepted architecture does not prescribe:

1. The exact task assessment representation.
2. Whether planning profiles use a formal scoring model.
3. The plan revision identifier format.
4. The criteria for distinguishing material and nonmaterial revisions.
5. The initial approval event vocabulary.
6. The algorithm for Work Unit decomposition.
7. The default planning budgets.
8. The representation of unresolved hypotheses.
9. The user interface for approval checkpoints.
10. The mechanism for evaluating AI planning quality.
11. The policy for automatic profile escalation recommendations.
12. The exact serialization format for internal plan artifacts.

These decisions should be resolved during implementation when supported by concrete requirements.

They must preserve the architectural invariants established above.

---

## 25. Acceptance and Compliance

ADR-012 is accepted as part of the AEW v0.1 architecture.

Implementation is compliant when it demonstrates that:

- Quick, Standard, Deep, and Explore profiles are supported.
- Planning effort is proportional to task characteristics.
- Simple tasks do not require unnecessary documentation overhead.
- High-risk tasks receive appropriate investigation and review.
- Material plan revisions are traceable.
- Context Package identity is preserved.
- Work Units remain associated with their plan revisions.
- Scope changes trigger authorization reassessment.
- Scoped approvals avoid unnecessary repeated authorization.
- Explore tasks can remain read-only.
- Planning does not independently grant execution authority.

Compliance requires observed verification evidence.

The existence of this ADR does not establish that these capabilities have been implemented.

---

## 26. Decision Summary

AEW uses adaptive planning profiles to match engineering process depth to actual task requirements.

Quick supports localized low-risk changes.

Standard supports ordinary engineering implementation.

Deep supports complex, high-risk, or architecturally significant work.

Explore supports investigation without an implementation commitment.

Plans are revisioned, grounded in immutable Context Packages, and decomposed into meaningful Work Units when appropriate.

Material changes require reassessment of applicable authorization.

Human approval occurs at meaningful decision and execution boundaries rather than after every routine operation.

**AEW should apply as much engineering process as necessary to preserve correctness and control—and no more than the task justifies.**