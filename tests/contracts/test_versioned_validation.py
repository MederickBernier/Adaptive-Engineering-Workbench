"""Exercise version dispatch, declared binding rejection, and legacy compatibility."""

import copy
import hashlib
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from referencing.exceptions import NoSuchResource

from contracts.validation import (
    EXTENSION_CONTRACTS,
    LEGACY_CONTRACTS,
    ContractError,
    content_digest,
    load_json,
    schema_path,
    schema_registry,
    validate_bundle,
    validate_document,
)
from engine.context.package import ContextPackage, ContextPackageError
from engine.execution.authority import (
    OPERATIONS,
    ApprovalGrant,
    GrantVerifier,
    SignedGrant,
    WorkspaceBinding,
)
from engine.execution.checkpoint import CheckpointStore
from engine.execution.envelope import ExecutionBudget, ExecutionEnvelope

ROOT = Path(__file__).resolve().parents[2]
FAMILY = ROOT / "contracts/v0.2"


@pytest.fixture
def bundle() -> dict:
    return load_json(FAMILY / "bundles/delegated.json")


@pytest.mark.parametrize("name", ["delegated", "read-only"])
def test_complete_workflow_examples(name: str) -> None:
    validate_bundle(load_json(FAMILY / "bundles" / f"{name}.json"))


@pytest.mark.parametrize("contract", EXTENSION_CONTRACTS)
def test_versioned_fixtures_use_public_dispatch(contract: str) -> None:
    for fixture in (FAMILY / "examples").glob(f"{contract}.*.json"):
        document = load_json(fixture)
        if ".invalid-" in fixture.name:
            with pytest.raises(ContractError):
                validate_document(contract, document)
        else:
            validate_document(contract, document)


def test_legacy_fixtures_and_new_family_are_explicitly_selected() -> None:
    for contract in LEGACY_CONTRACTS:
        for path in (ROOT / "contracts/examples").glob(f"{contract}.*.json"):
            if ".invalid-" not in path.name:
                validate_document(contract, load_json(path))
    for version in (None, "0.3", 0.2):
        with pytest.raises(ContractError, match="Unsupported"):
            validate_document("task", {"schema_version": version})
    with pytest.raises(ContractError, match="Unsupported"):
        schema_path("../../outside", "0.2")
    with pytest.raises(ContractError, match="Unsupported"):
        schema_path("agent-profile", "0.1")


def test_registry_never_retrieves_network_resources() -> None:
    with pytest.raises(NoSuchResource):
        schema_registry().get_or_retrieve("https://unavailable.example/schema.json")


@pytest.mark.parametrize(
    "raw",
    [
        '{"schema_version":"0.2","schema_version":"0.1"}',
        '{"value":NaN}',
        '{"value":Infinity}',
        "[]",
    ],
)
def test_json_ingress_rejects_ambiguous_or_nonfinite_content(
    tmp_path: Path, raw: str
) -> None:
    path = tmp_path / "document.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ContractError):
        load_json(path)


def test_malformed_timestamp_and_unknown_fields_fail_structure(bundle: dict) -> None:
    grant = bundle["approval"]
    grant["expires_at"] = "tomorrow"
    with pytest.raises(ContractError):
        validate_document("approval", grant)
    grant["expires_at"] = "2099-01-01T00:00:00Z"
    grant["authorization"]["unrestricted"] = True
    with pytest.raises(ContractError):
        validate_document("approval", grant)


SEMANTIC_MUTATIONS = [
    (("task", "task", "repository"), "other/repository"),
    (("task", "plan", "revision"), 2),
    (("task", "assessment", "profile"), "explore"),
    (("task", "plan", "delegation", "max_concurrent_agents"), 6),
    (("task", "plan", "work_units", 0, "id"), "unknown-unit"),
    (("context", "identity", "revision", "snapshot_id"), "other-snapshot"),
    (("context", "identity", "revision", "workspace_fingerprint"), "other-fingerprint"),
    (("context", "observation", "candidate", "digest"), "sha256:" + "9" * 64),
    (("approval", "status"), "revoked"),
    (("approval", "revoked_at"), "2026-01-02T00:00:00Z"),
    (("approval", "expires_at"), "2025-01-01T00:00:00Z"),
    (
        ("approval", "authorization", "operations"),
        ["implement", "run_tests", "review", "apply_candidate"],
    ),
    (("approval", "authorization", "delegation", "max_total_agent_launches"), 1),
    (("execution", "context", "package_id"), "other-context"),
    (("execution", "scope", "allowed_paths"), ["other/**"]),
    (("execution", "scope", "protected_paths"), []),
    (("execution", "runtime_approval_id"), "other-approval"),
    (("execution", "budget", "max_tool_calls"), 21),
    (("agent-profile", "profile_revision"), "2"),
    (("agent-profile", "restrictions"), ["implement"]),
    (("agent-assignment", "context_id"), "other-context"),
    (("agent-assignment", "allowed_paths"), ["other/**"]),
    (("agent-assignment", "budget", "max_duration_seconds"), 301),
    (("child-authority", "parent_grant_id"), "other-grant"),
    (("child-authority", "operations"), ["push"]),
    (("child-authority", "protected_paths"), []),
    (("child-authority", "allowed_paths"), ["other/**"]),
    (("child-authority", "budget", "max_tool_calls"), 21),
    (("child-authority", "expires_at"), "2100-01-01T00:00:00Z"),
    (("child-authority", "delegation_depth"), 2),
    (("child-authority", "status"), "suspended"),
    (("sandbox", "resources", "cpu_millicores"), 2000),
    (("runtime-capability", "runtime_version"), "different-runtime"),
    (("runtime-capability", "controls"), ["network_deny"]),
    (("runtime-evidence-approval", "status"), "withdrawn"),
    (("runtime-evidence-approval", "configuration_digest"), "sha256:" + "8" * 64),
    (("runtime-evidence-approval", "evidence_digests"), ["sha256:" + "8" * 64]),
    (("agent-result", "changes", 0, "path"), "src/private/secret.py"),
    (("agent-result", "changes", 0, "change_type"), "deleted"),
    (("agent-result", "findings", 0, "observation", "base_commit"), "b" * 40),
    (
        ("delivery", "work_units", 0, "verification", 0, "candidate", "digest"),
        "sha256:" + "7" * 64,
    ),
    (
        ("delivery", "work_units", 0, "verification", 0, "requirements_digest"),
        "sha256:" + "7" * 64,
    ),
    (("delivery", "work_units", 0, "verification"), []),
    (("delivery", "work_units", 0, "reviews", 0, "outcome"), "changes_requested"),
    (("delivery", "work_units", 0, "reviews", 0, "reviewer_kind"), "agent"),
    (("delivery", "work_units", 0, "reviews"), []),
]


@pytest.mark.parametrize(
    ("path", "value"), SEMANTIC_MUTATIONS, ids=lambda item: str(item)
)
def test_structurally_valid_inconsistent_bindings_are_rejected(
    bundle: dict, path: tuple, value: object
) -> None:
    target = bundle
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    for name, document in bundle.items():
        validate_document(name, document)
    with pytest.raises(ContractError):
        validate_bundle(bundle)


def test_incomplete_or_mixed_families_fail_closed(bundle: dict) -> None:
    del bundle["runtime-evidence-approval"]
    with pytest.raises(ContractError, match="Incomplete"):
        validate_bundle(bundle)
    bundle["context"]["schema_version"] = "0.1"
    with pytest.raises(ContractError, match="family"):
        validate_bundle(bundle)


def test_structure_and_binding_validation_do_not_authenticate_records(
    bundle: dict,
) -> None:
    for name in ("approval", "child-authority", "runtime-evidence-approval"):
        bundle[name]["proof"]["signature"] = "f" * 64
    validate_bundle(bundle)


def test_cross_purpose_record_proof_is_rejected(bundle: dict) -> None:
    bundle["runtime-evidence-approval"]["proof"]["domain"] = "aew-approval-v0.2"
    with pytest.raises(ContractError):
        validate_document(
            "runtime-evidence-approval", bundle["runtime-evidence-approval"]
        )


def test_specialization_composition_preserves_profile_revision(bundle: dict) -> None:
    bundle["agent-assignment"]["specializations"] = [
        {
            "label": "java",
            "basis": "Engineer-selected expertise",
            "evidence_references": ["engineer:request"],
        }
    ]
    validate_bundle(bundle)
    assert bundle["agent-profile"]["profile_revision"] == "1"


def test_duplicate_specialization_labels_are_rejected(bundle: dict) -> None:
    bundle["agent-assignment"]["specializations"].append(
        {
            "label": "python",
            "basis": "Additional selection",
            "evidence_references": ["engineer:request"],
        }
    )
    with pytest.raises(ContractError, match="Unique specialization labels"):
        validate_bundle(bundle)


def _seal_candidate(bundle: dict) -> None:
    manifest = bundle["delivery"]["candidate_manifest"]
    payload = {key: value for key, value in manifest.items() if key != "candidate"}
    payload["base_commit"] = manifest["candidate"]["base_commit"]
    payload["workspace_fingerprint"] = manifest["candidate"]["workspace_fingerprint"]
    digest = content_digest(payload)

    def update(value: object) -> None:
        if isinstance(value, dict):
            if "candidate_id" in value:
                value["digest"] = digest
            for child in value.values():
                update(child)
        elif isinstance(value, list):
            for child in value:
                update(child)

    update(bundle)


@pytest.mark.parametrize(
    "path", ["src/private/secret.py", "other/outside.py", ".git/config"]
)
def test_integration_edits_are_checked_after_candidate_integrity(
    bundle: dict, path: str
) -> None:
    bundle["delivery"]["candidate_manifest"]["files"][0]["path"] = path
    bundle["delivery"]["candidate_manifest"]["resolution_references"] = [
        "integration-decision-1"
    ]
    _seal_candidate(bundle)
    with pytest.raises(ContractError):
        validate_bundle(bundle)


@pytest.mark.parametrize("status", ["commit_proposed", "awaiting_commit", "committed"])
@pytest.mark.parametrize("outcome", ["failed", "incomplete", "not_run"])
def test_every_ready_state_requires_successful_checks(
    bundle: dict, status: str, outcome: str
) -> None:
    unit = bundle["delivery"]["work_units"][0]
    unit["status"] = status
    unit["verification"][0]["status"] = outcome
    unit["verification"][0]["reason"] = "Required check did not pass"
    validate_document("delivery", bundle["delivery"])
    with pytest.raises(ContractError, match="verification is incomplete"):
        validate_bundle(bundle)


def test_failed_checks_can_be_reported_honestly_without_readiness(bundle: dict) -> None:
    unit = bundle["delivery"]["work_units"][0]
    unit["status"] = "not_ready"
    unit["verification"][0]["status"] = "failed"
    unit["verification"][0]["reason"] = "Observed nonzero exit"
    validate_bundle(bundle)


def test_missing_candidate_evidence_is_a_structural_error(bundle: dict) -> None:
    del bundle["delivery"]["work_units"][0]["verification"][0]["candidate"]
    with pytest.raises(ContractError):
        validate_document("delivery", bundle["delivery"])


def test_final_file_boundary_cannot_differ_from_candidate(bundle: dict) -> None:
    bundle["delivery"]["work_units"][0]["change_boundary"]["files"][0]["after_hash"] = (
        "sha256:" + "8" * 64
    )
    with pytest.raises(ContractError, match="Final candidate file boundary"):
        validate_bundle(bundle)


def test_application_gate_evidence_is_bound(bundle: dict) -> None:
    unit = bundle["delivery"]["work_units"][0]
    gate = {
        "candidate": copy.deepcopy(unit["candidate"]),
        "requirements_digest": unit["requirements"]["digest"],
        "verification_ids": ["evidence-1"],
        "review_ids": ["human-review-1"],
    }
    bundle["execution"]["application_gate"] = gate
    validate_bundle(bundle)
    gate["verification_ids"] = ["unrelated-evidence"]
    with pytest.raises(ContractError, match="Application gate evidence"):
        validate_bundle(bundle)


def test_partial_results_and_read_only_results_have_explicit_shapes(
    bundle: dict,
) -> None:
    result = bundle["agent-result"]
    result["status"] = "cancelled"
    result["partial"] = True
    validate_document("agent-result", result)
    result["partial"] = False
    with pytest.raises(ContractError):
        validate_document("agent-result", result)
    result["partial"] = True
    result["access_mode"] = "read_only"
    result["changes"] = []
    result["artifacts"] = []
    validate_document("agent-result", result)


def test_read_only_delivery_cannot_claim_publication_or_unexecuted_checks() -> None:
    documents = load_json(FAMILY / "bundles/read-only.json")
    documents["delivery"]["publication"]["stage"] = {
        "status": "authorized",
        "grant_id": "grant-1",
    }
    with pytest.raises(ContractError):
        validate_document("delivery", documents["delivery"])
    documents["delivery"]["publication"]["stage"] = {"status": "not_authorized"}
    documents["execution"]["verification"]["required_checks"] = [
        {"id": "required-read", "description": "Read evidence", "required": True}
    ]
    with pytest.raises(ContractError, match="read-only verification"):
        validate_bundle(documents)


@pytest.mark.parametrize(
    "timestamp",
    [
        "tomorrow",
        "2026-02-30T00:00:00Z",
        "2026-01-01T00:00:00",
        "2026-01-01 00:00:00Z",
        "2026-01-01T00:00:00+00:99",
        "2026-01-01T00:00:00+23:60",
    ],
)
def test_timestamp_checks_are_independent_of_optional_format_packages(
    bundle: dict, timestamp: str
) -> None:
    bundle["approval"]["issued_at"] = timestamp
    with pytest.raises(ContractError):
        validate_document("approval", bundle["approval"])


def test_candidate_requirements_cannot_silently_drop_execution_checks(
    bundle: dict,
) -> None:
    requirements = bundle["delivery"]["candidate_manifest"]["requirements"]
    requirements["required_checks"] = []
    requirements["digest"] = content_digest(
        {key: value for key, value in requirements.items() if key != "digest"}
    )
    bundle["task"]["plan"]["work_units"][0]["requirements"] = copy.deepcopy(
        requirements
    )
    bundle["delivery"]["work_units"][0]["requirements"] = copy.deepcopy(requirements)
    bundle["approval"]["requirements_digest"] = requirements["digest"]
    for record in (
        bundle["delivery"]["work_units"][0]["verification"]
        + bundle["delivery"]["work_units"][0]["reviews"]
    ):
        record["requirements_digest"] = requirements["digest"]
    _seal_candidate(bundle)
    with pytest.raises(ContractError, match="Execution verification requirements"):
        validate_bundle(bundle)


def test_application_outcome_requires_permission_and_exact_gate(bundle: dict) -> None:
    unit = bundle["delivery"]["work_units"][0]
    unit["application"] = {
        "status": "applied",
        "grant_id": "grant-1",
        "candidate": copy.deepcopy(unit["candidate"]),
        "evidence_id": "application-evidence-1",
    }
    validate_bundle(bundle)
    bundle["approval"]["authorization"]["operations"].remove("apply_candidate")
    with pytest.raises(ContractError, match="application permission"):
        validate_bundle(bundle)


def test_legacy_schema_fixture_and_runtime_identities_are_preserved() -> None:
    golden = load_json(Path(__file__).parent / "fixtures/legacy-compatibility.json")
    for name, digest in golden["normalized_file_hashes"].items():
        assert (
            hashlib.sha256(
                (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            == digest
        )
    workspace = WorkspaceBinding("example/project", "master", "a" * 40, "checkout")
    now = datetime(2026, 1, 1, tzinfo=UTC)
    grant = ApprovalGrant(
        "legacy-grant",
        "engineer",
        "task-1",
        1,
        workspace,
        ("unit-1",),
        ("investigate",),
        ("src/**",),
        (),
        now,
        now + timedelta(minutes=5),
    )
    signed = SignedGrant(grant, bytes.fromhex(golden["grant_signature"]))
    assert (
        GrantVerifier("engineer", b"k" * 32, is_revoked=lambda _: False).verify(
            signed, now=now
        )
        == grant
    )
    envelope = ExecutionEnvelope(
        "exec",
        "task-1",
        1,
        "unit-1",
        "ctx",
        "snapshot",
        "legacy-grant",
        workspace,
        "fingerprint",
        ("investigate",),
        ("src/**",),
        ExecutionBudget(1, 3, 100),
    )
    assert CheckpointStore._binding(envelope) == golden["checkpoint_binding"]
    content = load_json(ROOT / "contracts/examples/context.basic.json")
    del content["package_id"]
    assert ContextPackage.create(content).package_id == golden["context_id"]
    assert "delegate" not in OPERATIONS
    new_content = load_json(FAMILY / "examples/context.basic.json")
    del new_content["package_id"]
    with pytest.raises(ContextPackageError, match="Unsupported"):
        ContextPackage.create(new_content)


@pytest.mark.parametrize(
    "arguments",
    [
        ["document", "task", "contracts/examples/task.quick.json"],
        [
            "document",
            "agent-profile",
            "contracts/v0.2/examples/agent-profile.basic.json",
        ],
        ["bundle", "contracts/v0.2/bundles/delegated.json"],
    ],
)
def test_validator_cli_entry_points(arguments: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "-B", "-m", "contracts.validation", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "validated" in result.stdout


def test_validator_cli_rejects_invalid_contract() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "contracts.validation",
            "document",
            "sandbox",
            "contracts/v0.2/examples/sandbox.invalid-boundary.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Validation failed" in result.stderr
