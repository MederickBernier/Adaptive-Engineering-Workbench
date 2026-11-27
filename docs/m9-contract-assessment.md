# M9 Work Unit 1 — Contract and Consumer Assessment

**Status:** Assessment complete, all six proposals approved on 2026-11-26

**Baseline:** `a93b9ac` on `master`

**Date:** 2026-11-26

**Authorized scope:** Read-only assessment and Markdown documentation

## 1. Findings and review boundary

The five existing contracts use JSON Schema Draft 2020-12, fixed `schema_version: "0.1"`, unversioned schema IDs, and closed objects at the extension points examined. Delegation and candidate fields require versioned contract changes. The engine also uses typed runtime representations whose fields, signatures, and persistence bindings differ from the JSON contracts.

The engineer approved all six recommendations on 2026-11-26 and authorized only Work Unit 2, versioned contracts and validation. This document retains the assessment and proposed migration sequence as the review record. The [0.2 contract family](../contracts/v0.2/README.md) records the delivered validation interfaces. Work Units 3–4 and runtime implementation remain paused. Accepted requirements come from [ADR-013](adr/ADR-013-adaptive-multi-agent-orchestration.md), [ADR-014](adr/ADR-014-composable-agent-profiles.md), [ADR-015](adr/ADR-015-sandbox-isolation.md), [ADR-016](adr/ADR-016-coordination-and-delegated-authority.md), and [ADR-017](adr/ADR-017-result-reconciliation-and-integration.md).

## 2. Existing contracts and consumers

| Contract | Producers and consumers inspected | Compatibility impact |
|---|---|---|
| [Task](../contracts/task.schema.json) | [PlanDraft.to_task_document](../engine/planning/plan.py), [PlanHistory](../engine/planning/history.py), [intake](../engine/workflow/intake.py), [CLI](../engine/workflow/cli.py), [TaskHost](../engine/workflow/host.py), contract and planning tests | Producers emit 0.1. Required-action enums lack delegation, separate review, and candidate application. Plans have no explicit delegation or agent-count fields. New fields must enter material-change detection and immutable plan revisioning. |
| [Context](../contracts/context.schema.json) | [ContextPackage](../engine/context/package.py), [assembly](../engine/context/assembly.py), [expand_context](../engine/context/expansion.py), planning, execution policy, intake, CLI, context and integration tests | The codec accepts only 0.1 and hashes canonical content, including its version. Revision records allow a workspace fingerprint but lack candidate identity. Expansion requires exactly matching identity, including revision and snapshot. Candidate transitions require explicit successor construction and execution rebinding. |
| [Approval](../contracts/approval.schema.json) | Contract fixtures and [test-only semantic validation](../tests/contracts/test_semantics.py). Operational authority uses [ApprovalGrant, SignedGrant, TrustedGrantIssuer, and GrantVerifier](../engine/execution/authority.py), consumed by policy, controllers, TaskHost, and delivery review | The JSON document and signed dataclass are separate representations. Their fields and nesting differ. The runtime operation allowlist also lacks delegation. Schema-valid approval documents cannot be converted directly into trusted runtime authority. |
| [Execution](../contracts/execution.schema.json) | Contract fixtures and semantic tests. Runtime [ExecutionEnvelope, ExecutionBudget, and ExecutionPolicy](../engine/execution/envelope.py) feed [controllers](../engine/execution/controller.py), [isolated checks](../engine/execution/isolated.py), [checkpoints](../engine/execution/checkpoint.py), [change preparation](../engine/execution/changes.py), TaskHost, and delivery | The typed envelope is a distinct interface with no general JSON-contract decoder. Existing budgets cover iterations, tool calls, and duration. Parent/child authority, runtime eligibility, candidate bindings, and task-wide agent counts need representation. Schema `delivery.prepare_commit` is fixed to true. |
| [Delivery](../contracts/delivery.schema.json) | [propose_commit](../engine/delivery/proposal.py), [prepare_delivery and review_progress](../engine/delivery/draft.py), [resolve_checks](../engine/delivery/verification.py), TaskHost, delivery and integration tests | Producers emit 0.1 with per-file hashes and trusted check references. Explicit combined-candidate, runtime-approval, and accepted-review references are absent. Current review checkpoints require a signed grant containing `commit`, while publication status remains separately unauthorized. Versioned review and application semantics need distinct bindings. |

The [task skill](../aew/skills/aew-task/SKILL.md) describes retaining the returned plan and Context Package and using trusted-host operations. Its handoff examples will require version and candidate guidance when those interfaces become supported. Git preflight and source discovery provide upstream observations and remain relevant to regression coverage.

### 2.1 Validation and fixture consumers

[Schema tests](../tests/contracts/test_schemas.py) explicitly enumerate the five current schema filenames and discover examples under `contracts/examples`. Adding schema files alone will leave them outside that enumeration. [Semantic helpers](../tests/contracts/test_semantics.py) are test code and check selected identities, operation subsets, approval status, and exact path membership. Production authorization uses separate policy and filesystem logic.

Context, planning, and delivery tests validate emitted documents against their 0.1 schemas. The Context Package codec verifies binding and canonical identity independently of full JSON Schema validation. The runtime has no general registry routing all five wire contracts into typed objects. [pyproject.toml](../pyproject.toml) declares `jsonschema` as a development dependency.

### 2.2 Persistence and cryptographic compatibility

- Context IDs hash canonical package content. Changing the version or candidate observation creates a new ID. Existing packages retain their original bytes and identities.
- `authority._signature` signs a canonical dataclass payload with the `aew-approval-v1` domain. Optional absent `review_digest` is specially omitted. Adding dataclass fields can change existing signatures even when callers supply defaults.
- `CheckpointStore._binding` hashes `asdict(envelope)`. Adding defaulted envelope fields can invalidate existing checkpoint bindings. Budget state and uncertain outcomes must survive migration.
- PlanHistory retains immutable JSON plan revisions and compares material boundaries. New delegation, candidate, and resource fields must participate in that comparison.
- `CheckEvidence` binds task, plan revision, Work Unit, execution, repository, commit, change-review digest, check, image, and observation time. It lacks a versioned runtime-evidence approval reference and combined-candidate identity.
- `IsolatedChecks` also fingerprints replacements, check arguments, and image for checkpoint matching. Delivery review separately hashes proposal content. These identities must retain their original meaning through migration.

## 3. Observed compatibility probes

In-memory copies of valid current fixtures were modified and validated with the unchanged schemas. Every original fixture used by these probes was valid.

| Probe | Observed rejection |
|---|---|
| Add `delegate` to Approval authorization operations | `enum` |
| Set Execution `delivery.prepare_commit` to false | `const` |
| Add Task `plan.delegation` | `additionalProperties` |
| Add Context `identity.revision.candidate_id` | `additionalProperties` |
| Add Delivery Work Unit `candidate_id` | `additionalProperties` |
| Set `schema_version` to 0.2 in each of the five original fixture families | `const` in all five schemas |

The read-only delivery conflict is already documented in ADR-010. The typed runtime envelope has no delivery-preparation field, and Explore uses committed reads through TaskHost. Fixing the wire contract therefore requires a consumer and serialization decision alongside the schema correction.

## 4. Versioning proposal for review

### 4.1 Preserve the 0.1 interfaces and add a 0.2 contract family

Keep existing schema paths, IDs, fixtures, stored documents, and canonicalization rules available for 0.1 consumers. Introduce the extension under `contracts/v0.2/`, with unique IDs such as `https://aew.local/schemas/0.2/context.schema.json` and explicit `schema_version: "0.2"`. Apply the same family version to the new contract types. This is a proposed wire-contract version and is independent of the application release number and ADR document versions.

Use explicit version routing at JSON boundaries and local schema resolution. Reject unsupported versions and incompatible family combinations. A selected 0.1 reference may appear as historical evidence with its own identity and applicability record, while live delegated bindings require validated 0.2 representations. Preserve strict unknown-field rejection and avoid overloading notes, evidence descriptions, or autonomy levels with executable permissions.

Optional delegation and candidate sections preserve ordinary single-agent use in 0.2. When delegation or a candidate observation is requested, the applicable fields become required and must pass semantic and authority checks. Unknown capability names fail closed. This family-wide strategy allows explicit upgrade of coordinated records without silently changing current callers.

### 4.2 Proposed changes to the five contracts

| Contract | Proposed 0.2 representation and enforcement requirement |
|---|---|
| Task | Add a bounded delegation section containing intent, finite concurrent-agent and total-launch limits, and references to assignment planning. Add `delegate`, `review`, and `apply_candidate` to the action vocabulary with separate purposes. Include these fields in material-change detection and approval reassessment. |
| Context | Add an explicit observation kind and candidate reference containing identity, baseline commit, and workspace fingerprint, alongside the actual source Brain snapshot. Preserve per-evidence revision provenance and a successor package reference. Candidate changes require new sealed packages and explicit execution-context transitions. |
| Approval | Represent explicit delegation permission and its bounds in trusted authorization. Bind child authority to its parent, assignment, effective restrictions, and validity. Review acceptance binds the exact candidate and requirements, and candidate application has separate scoped authority. Verify authenticity and live status through the trusted host. |
| Execution | Bind assignment, parent execution, child authority, runtime capability revision, evidence approval, sandbox configuration, and candidate observation where applicable. Represent finite task-wide counts and their parent accounting identity alongside per-execution resources. Allow read-only delivery with `prepare_commit: false` and disabled publication. Define the application gate against current mandatory checks and reviews. |
| Delivery | Add candidate identity and manifest references, result-package lineage, current requirements identity, verification and accepted-review references, and application outcome evidence. Include a read-only outcome without artificial commit or PR proposals. Keep publication observations separately recorded. |

M9 defines and validates these representations. Operational support for specialist launch belongs to M10, adaptive aggregate admission to M11, and candidate integration and application to M12. Runtime operation names remain subject to supported guarded adapters even after a vocabulary is defined.

### 4.3 New contract and record representations

| Representation | Minimum content proposed for schema review |
|---|---|
| Agent Profile | Immutable profile and role identity/revision, primary responsibility, deliverables, capability limits, restrictions, and specialization labels with selection provenance recorded by assignments. |
| Agent Assignment | Task, plan revision, Work Unit, parent execution, profile revision, immutable context, baseline/candidate observation, delegated authority, sandbox and runtime references, resource allocation, count-accounting identity, dependencies, and idempotent request identity. |
| Sandbox | Immutable configuration identity/digest, workspace baseline, filesystem and process controls, permitted mounts and network, resource limits, runtime identity, and eligibility references. |
| Agent Result | Immutable manifest, assignment and authority lineage, context and observation identity, outcome, artifact identities/digests, findings, changes, evidence, verification, and limitations. Read-only and partial results have explicit shapes. |
| Runtime Capability Description | Adapter/runtime versions, operating environment, immutable configuration, declared threat model, supported controls, limitations, and evidence references. |
| Runtime Evidence Approval | Trusted issuer, capability and evidence digests, exact approved environment/configuration, validity and live withdrawal reference, with integrity and authenticity verification. |
| Child Authority Record | Parent authority and execution, assignment, effective capabilities and scope, protected paths, resource and delegation bounds, validity, and trusted issuance evidence. |

Define candidate references and manifest contents within the reviewed versioned contract family, including baseline, final content identity, selected result revisions, resolution records, and workspace fingerprint. Define verification and review references carrying candidate and requirements identities plus their provenance. M12 will produce and enforce combined candidates through those interfaces.

Use a domain and canonicalization version specific to each trusted signed record type. Execution authorization, child authority, runtime approval, and review acceptance must remain distinguishable during verification. Exact cryptographic storage and issuer provisioning details require a reviewed design using the existing trusted-host model.

The current text adapter supports bounded UTF-8 file creation and replacement. Result capabilities must declare supported artifact and change kinds. Unsupported binary, rename, deletion, symlink, or arbitrary patch application requests must be rejected by the receiving adapter until that behavior is explicitly supported and verified.

## 5. Migration proposal and consumer sequence

1. Preserve current schema and fixture bytes. Add family-specific schema registration, fixture discovery, and explicit version dispatch. Extend schema, semantic, codec, and adapter tests together. Recommend using the existing Draft202012Validator library at new public JSON ingress boundaries, with a reviewed promotion of `jsonschema` from development to runtime dependencies. This reuses the tested schema definitions and adds a runtime dependency. Typed semantic, timestamp, and trusted-authority checks remain required. Keeping validation entirely in typed parsers would require maintaining and testing equivalent structural constraints separately.
2. Add explicit document-to-runtime mappings. Validate every normative constraint, rejecting unsupported constraints when a faithful runtime mapping is unavailable. JSON `approved_by` and status fields remain untrusted inputs until checked through trusted issuance.
3. Preserve legacy issuer/verifier behavior and canonical signatures. Existing grants retain their original authority, expiration, and revocation rules. Enabling delegation requires newly issued explicit authority. A legacy commit-scoped review checkpoint cannot become a new review acceptance or candidate-application grant through format conversion.
4. Preserve old package bytes, digests, and plan revisions. Upgrading creates new package identities and applicable plan revisions, with explicit lineage and revalidation. Keep old codecs available for supported historical reads and current legacy callers. Candidate adoption requires reviewed applicability and rebinding.
5. Retain the existing checkpoint binding algorithm for legacy records and define versioned bindings for new records. Preserve consumed budgets, pending operations, and evidence. A new envelope identity requires reconciliation of the previous execution before resource transfer or resumption. Ambiguous stored state must suspend affected work. Database migrations, if needed, require reviewed backups, transactional migration, and recovery coverage before use.
6. Keep existing ChangeReview, check-evidence, and delivery-review meanings intact. New candidate and runtime approval references create new evidence records. Historical evidence retains its observed subject and environment. Withdrawn isolation approval triggers applicability reassessment before dependent evidence can satisfy a new application gate.
7. Opt new producers into 0.2 only after their consumers, persistence bindings, and authority checks support it. Retain a legacy route for supported 0.1 workflows and deny delegation on that route. Retiring legacy support requires a separate reviewed compatibility decision.

## 6. Initial runtime eligibility boundary

The initial candidate is [DockerSandbox](../engine/execution/isolated.py), already configured with an absolute Docker executable, a pinned image ID, a selected local engine endpoint, disabled network, read-only root, dropped capabilities, a non-root user, resource limits, bounded tmpfs storage, and timeout cleanup. These are observations of current source. Fresh operating-system isolation evidence remains a later Work Unit deliverable.

TaskHost constructs IsolatedChecks around that adapter. The future eligibility check should validate the trusted runtime evidence approval before provisioning, guarded operations, and resumption. It must bind the actual executable/runtime, image, operating environment, adapter implementation, configuration, and demonstrated controls, and deny missing, stale, withdrawn, or inapplicable approval. Changes to controls require a new applicable capability/evidence approval binding.

Reuse the existing host-controlled signing and live status-check patterns after introducing record-type separation. Keep runtime administration and approval issuance under trusted host control. Pass eligibility observations through the existing mediated boundary and extend check evidence so downstream consumers can assess its applicability. Preserve the legacy isolated-check route under its documented guarantees while adding the new, explicitly selected orchestration eligibility path.

The later M10 launch interface should accept a validated immutable assignment and explicit trusted authority, verify runtime eligibility and finite resource/count admission, and return a traceable launch outcome and result reference. Provisioning, lifecycle coordination, and agent execution remain M10 work.

## 7. Proposed validation coverage

| Layer | Required future cases |
|---|---|
| Structural | Valid examples for every new representation, unknown fields and versions, invalid identifiers and digests, missing candidate fields, unsupported operation vocabulary, missing/invalid finite counts, and read-only delivery. |
| Semantic | Task/plan/Work Unit/parent mismatches, incompatible contract families, wrong snapshot or candidate fingerprint, profile revision drift, overbroad child scope, protected-path precedence, expired parent, and child validity exceeding parent validity. |
| Trusted authority | Forged and cross-purpose signatures, missing delegation permission, altered evidence approval, revoked or unavailable status, version/configuration mismatch, and failed evidence applicability. |
| Persistence and identity | Legacy golden signatures and package digests, unchanged old checkpoint bindings and consumed resources, immutable plan history, successor lineage, duplicate requests, interrupted migration, and explicit rebinding. |
| Consumer regression | Existing Task, Context, Approval, Execution, and Delivery fixtures and current entry points, supported legacy review behavior, honest unavailable checks, and separately enforced publication. |
| Runtime evidence | Real isolation, resource, network, filesystem, and cleanup checks on the selected configuration, with exact commands and provenance. These belong to later authorized runtime verification. |

## 8. Verification performed for this assessment

Executed the existing local environment command below with bytecode and pytest cache writes disabled.

```powershell
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/contracts tests/unit/test_controlled_execution.py tests/unit/test_context_package.py tests/unit/test_delivery.py tests/unit/test_planning.py
```

Observed result was **72 passed, 3 skipped**. The skipped cases are missing negative fixtures for Context, Execution, and Delivery. The in-memory compatibility probes in section 3 produced all expected rejections.

Source and fixture inspection establish current representation and dependency relationships. New 0.2 contracts, migration behavior, runtime eligibility, live isolation, provider launches, complete remote preflight, and broader Git/Docker integration remain unverified in this assessment. The existing Docker integration tests require `AEW_TEST_DOCKER_IMAGE` and were outside the selected baseline test command.

## 9. Decisions approved by the engineer

1. Adopt a side-by-side 0.2 contract family with immutable legacy schemas, explicit dispatch, and reviewed typed mappings.
2. Adopt separate delegation, review, and candidate-application purposes and operation names, with fresh authority for delegation and domain-separated trusted records.
3. Adopt candidate-specific context, evidence, review, and application bindings, including a read-only delivery representation.
4. Preserve legacy signatures, digests, plan revisions, checkpoint bindings, and resource consumption through explicit versioned migration paths.
5. Use the existing local Docker adapter as the first runtime candidate and establish trusted evidence approval at its host-mediated boundary.
6. Use Draft202012Validator at new public JSON ingress boundaries, subject to review of the proposed `jsonschema` runtime dependency promotion, while preserving separate typed semantic and authority enforcement.

The Work Unit 1 assessment is complete and its six decisions are approved. Work Unit 2 supplies versioned contracts and repository validation. Production JSON ingress, the approved runtime dependency promotion, typed mappings, persistence migration, runtime eligibility, and live verification remain subsequent work under the current runtime pause.
