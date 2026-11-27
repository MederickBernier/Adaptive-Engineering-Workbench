# ADR-014 — Composable Agent Profiles and Specialization

**Status:** Accepted  
**Document version:** 0.1.2  
**Architecture baseline:** AEW v0.1 with accepted orchestration extension  
**Accepted on:** 2026-11-26  
**Decision scope:** Versioned roles, composable specialization labels, and assignment profile resolution

## 1. Context

AEW needs to assign specialists by engineering responsibility and project context. A review might require Java, Spring Boot, concurrency, and transaction expertise at the same time. Composing these specializations around one reviewer role keeps the assignment clear without requiring a separate role for every combination.

This decision builds on [adaptive multi-agent orchestration](ADR-013-adaptive-multi-agent-orchestration.md), [Project Intelligence Profiles](ADR-006-project-intelligence-profile.md), and [controlled execution](ADR-010-controlled-execution.md).

## 2. Decision

AEW will use versioned roles with composable specialization labels. An Agent Profile defines one role, its expected deliverables, the capabilities it may request, and its restrictions. An Agent Assignment selects a specific profile revision and records the specializations needed for that Work Unit. Profile composition is independent of the provider that executes the assignment.

### 2.1 Roles define responsibility

Each assignment has one primary role. An Explorer submits findings, a Reviewer submits review evidence, and an Implementer submits scoped changes for integration. When a Work Unit requires independent verification, it uses a separate assignment.

AEW will start with a small set of versioned roles. The initial role catalog remains an implementation planning decision.

### 2.2 Specializations guide selection and context

Specialization labels describe expertise in languages, frameworks, systems, or engineering concerns. Tasks may compose labels from revision-scoped project evidence, explicit requirements, and engineer input. A central specialization taxonomy is unnecessary for the initial design.

The orchestrator records the basis for each selection so inferred specializations can be reviewed. The Project Intelligence Profile retains its distinction between verified observations, provisional conclusions, conflicts, and unknown characteristics. Selecting a label does not establish that the provider has demonstrated the expertise it describes.

### 2.3 Profiles bound capability requests

The engine validates requested capabilities against active authorization and policy, and applies tighter assignment restrictions where appropriate. For example, a reviewer may request repository reads and submit findings. Adding database transaction expertise preserves those capability limits.

Every specialist launch passes through the engine under ADR-013, including launches through provider-native subagents. Detailed delegated authority rules are governed by ADR-016.

### 2.4 Assignments pin the resolved profile

An assignment records its role identity and revision, profile identity and revision, selected specialization labels and their selection basis, and effective restrictions. Referenced profile and role revisions must remain immutable and retrievable for review.

Profile edits create new revisions for future assignments. A material change to an active assignment requires revalidation before execution continues.

Assignments that verify or review a combined candidate also record its immutable identity and workspace fingerprint. Their Context Packages preserve the baseline commit and source Brain snapshot, distinguish candidate-derived evidence, and follow the context transition rules in [ADR-017](ADR-017-result-reconciliation-and-integration.md). Adopting a different candidate requires an explicit, engine-validated context transition under ADR-009.

## 3. Consequences

Versioned roles allow responsibilities to evolve while preserving the meaning of recorded assignments. Composable labels support project-specific expertise and reduce the number of profiles AEW must maintain.

Selection quality depends on evidence and provider suitability. AEW must preserve the provenance of inferred labels and evaluate specialist results through the Work Unit's verification requirements.

## 4. Verification criteria

- AEW can compose a Java concurrency reviewer from a Reviewer role and trace why each specialization was selected.
- Adding a specialization cannot expand effective permissions.
- A role or profile revision created after launch cannot silently change an active assignment.
- An unknown role or profile revision, or an unsupported required capability, is rejected before provisioning.
- The same profile can run through different eligible providers, subject to ADR-013's launch requirements.
- Independent verification uses a separate assignment when required by the Work Unit.
- Candidate verification and review assignments identify the candidate observation and use explicitly validated context transitions when that observation changes.

## 5. Follow-on decisions

Sandbox isolation, delegated authority, and result reconciliation are governed by ADR-015 through ADR-017. Versioned schemas for profiles and assignments require a later implementation assignment and contract review.
