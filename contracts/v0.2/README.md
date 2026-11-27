# AEW 0.2 Contracts and Validation

M9 Work Unit 2 supplies Draft 2020-12 schemas and repository validation tooling for the accepted orchestration design. The original five 0.1 schema paths, IDs, fixtures, runtime objects, signatures, package identities, and checkpoint bindings retain their existing behavior.

## Contract family

| Contract | Purpose |
|---|---|
| [Task](task.schema.json) | Plan revision, Work Units, delegation intent, limits, and recorded requirements |
| [Context](context.schema.json) | Source snapshot, committed or candidate observation, and successor identity |
| [Approval](approval.schema.json) | Explicit delegation permission, scoped operations, resource bounds, and signed-record metadata |
| [Execution](execution.schema.json) | Assignment, authority, runtime, observation, budget, and application-gate bindings |
| [Delivery](delivery.schema.json) | Candidate manifest, contribution dispositions, required checks and reviews, read-only findings, and application/publication observations |
| [Agent Profile](agent-profile.schema.json) | Versioned role and profile, capability limits, supported changes, and specialization labels |
| [Agent Assignment](agent-assignment.schema.json) | Bounded objective bindings, selected specializations and provenance, resources, and request identity |
| [Sandbox](sandbox.schema.json) | Versioned configuration, network, filesystem, process, and resource requirements |
| [Agent Result](agent-result.schema.json) | Result identity, observation, artifacts, findings, changes, outcome, and limitations |
| [Runtime Capability](runtime-capability.schema.json) | Runtime/environment/configuration identity, controls, threat model, evidence, and limitations |
| [Runtime Evidence Approval](runtime-evidence-approval.schema.json) | Issuer, approved capability and evidence, environment, validity, withdrawal reference, and proof metadata |
| [Child Authority](child-authority.schema.json) | Parent authority, assignment, effective restrictions, limits, validity, and proof metadata |

[Shared definitions](common.schema.json) contain the candidate manifest, candidate and requirements references, declared verification results, review acceptances, and common value types. They are resolved locally with the public schemas. Each public type has positive and negative fixtures under `examples/`.

## Entry points

From the repository root, use the existing development environment.

```powershell
.venv/Scripts/python.exe -B -m contracts.validation document task contracts/examples/task.quick.json
.venv/Scripts/python.exe -B -m contracts.validation document agent-profile contracts/v0.2/examples/agent-profile.basic.json
.venv/Scripts/python.exe -B -m contracts.validation bundle contracts/v0.2/bundles/delegated.json
.venv/Scripts/python.exe -B -m contracts.validation bundle contracts/v0.2/bundles/read-only.json
```

The document entry point selects the schema by the explicit contract name and the document's `schema_version`. Unsupported names and versions are rejected. The registry contains local resources and rejects external schema retrieval. JSON loading rejects duplicate keys and non-finite numbers. The 0.2 date-time profile uses uppercase `T` and `Z` or an explicit offset, with calendar and timezone validation independent of optional format-checking packages.

The bundle entry point checks a 0.2 workflow's declared relationships for one active Work Unit, with at most one assignment and one selected result package. A plan may contain other Work Units. Records are keyed by contract name, as shown in the two `bundles/` examples. Multi-assignment artifact resolution belongs to the later orchestration and integration interfaces.

Checks include task/repository/revision identity, immutable observation references, profile pins, explicit delegation permission, inherited operations and protected paths, resource and depth bounds, validity interval containment, runtime configuration and evidence references, candidate requirements, full final scope, and declared verification/review outcomes. A read-only result can report `findings_ready` with an empty change boundary and a `not_requested` PR status. A failed or unavailable required check can be represented honestly while readiness remains blocked.

## Canonical identities and proof records

Canonical JSON uses sorted object keys, ASCII escaping, compact comma/colon separators, finite values, and UTF-8 bytes. SHA-256 digests are represented as `sha256:` followed by 64 lowercase hexadecimal digits. Array order is preserved.

- A requirements digest covers its object with `digest` omitted.
- A capability digest covers its complete record with `digest` omitted.
- A sandbox configuration digest covers its record with `schema_version`, `sandbox_id`, `configuration_digest`, `repository`, `observation`, `capability_id`, and `runtime_approval_id` omitted. This isolates enforceable runtime configuration from assignment-specific identities.
- A candidate digest covers its manifest with `candidate` omitted, then adds the candidate's `base_commit` and `workspace_fingerprint`. Candidate identity, final file hashes, requirements, selected result IDs, contribution dispositions, and resolution references remain traceable through those records.

The proof representation follows the current host's HMAC-SHA256 algorithm and declares `aew-canonical-json-v1`. Domains distinguish `aew-approval-v0.2`, `aew-child-authority-v0.2`, `aew-runtime-approval-v0.2`, and `aew-review-acceptance-v0.2`. These are versioned wire representations for future trusted-host integration. Signed-record issuance, key storage, signature verification, and live status enforcement require the later runtime Work Unit.

All example proof signatures are fictional placeholders. Document validation establishes structure. Bundle validation additionally establishes consistency of supplied declarations and the specified content digests. Runtime authority still requires trusted issuance and current policy, revocation, eligibility, and state checks. Artifact bytes, package storage immutability, actual process isolation, consumed resources, current clock validity, and successful checkout application require observed runtime evidence.

## Compatibility and migration boundary

The existing engine continues to consume its 0.1 interfaces. The repository validator uses the existing development installation of `jsonschema`. Production JSON ingress, the approved runtime dependency promotion, typed mappings, and persistence migration remain part of subsequent runtime work. A legacy grant cannot acquire delegation permission through format conversion. Candidate adoption creates new context and evidence identities with explicit rebinding.

Golden regression fixtures protect normalized legacy schema/example content, an existing signed grant, a canonical Context Package ID, and an execution checkpoint binding. Local preservation checks also compare the original file bytes. The [assessment](../../docs/m9-contract-assessment.md) records the reviewed migration requirements, and the [handoff](../../docs/codex-handoff.md) records the active Work Unit boundary.

## Verification

```powershell
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/contracts
.venv/Scripts/python.exe -B -m ruff check contracts tests/contracts
.venv/Scripts/python.exe -B -m ruff format --check contracts tests/contracts
```

The contract suite checks both versions and all public 0.2 fixtures, local resolution, JSON ingress rejection, cross-contract negative cases, candidate readiness, scope, and legacy compatibility. The three original missing-negative-fixture skips remain associated with the unchanged 0.1 Context, Execution, and Delivery fixture sets.
