"""Validate wire documents locally, independently of runtime authorization."""

import argparse
import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from engine.git.preflight import ScopeExpression, ScopeKind, parse_scope

ROOT = Path(__file__).resolve().parent
LEGACY_CONTRACTS = ("task", "context", "approval", "execution", "delivery")
EXTENSION_CONTRACTS = (
    *LEGACY_CONTRACTS,
    "agent-profile",
    "agent-assignment",
    "sandbox",
    "agent-result",
    "runtime-capability",
    "runtime-evidence-approval",
    "child-authority",
)


class ContractError(ValueError):
    """A document has invalid structure or inconsistent declared bindings."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate JSON property: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ContractError(f"Non-finite JSON value: {value}")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_constant,
    )
    if not isinstance(value, dict):
        raise ContractError("Expected a JSON object")
    return value


def schema_path(contract: str, version: str) -> Path:
    if version == "0.1" and contract in LEGACY_CONTRACTS:
        return ROOT / f"{contract}.schema.json"
    if version == "0.2" and contract in EXTENSION_CONTRACTS:
        return ROOT / "v0.2" / f"{contract}.schema.json"
    raise ContractError(f"Unsupported contract/version: {contract}/{version}")


def _unavailable(uri: str) -> Resource:
    raise NoSuchResource(ref=uri)


def schema_registry() -> Registry:
    paths = [ROOT / f"{name}.schema.json" for name in LEGACY_CONTRACTS]
    paths.extend((ROOT / "v0.2").glob("*.schema.json"))
    resources = []
    for path in sorted(paths):
        document = load_json(path)
        resources.append((document["$id"], Resource.from_contents(document)))
    return Registry(retrieve=_unavailable).with_resources(resources)


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return True
    try:
        return datetime.fromisoformat(value).utcoffset() is not None
    except ValueError:
        return False


def validate_document(contract: str, document: dict[str, Any]) -> None:
    """Check structure. Successful validation grants no execution authority."""
    if not isinstance(document, dict):
        raise ContractError("Expected a contract object")
    try:
        json.dumps(document, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ContractError("Expected finite JSON content") from error
    version = document.get("schema_version")
    schema = load_json(schema_path(contract, version))
    checker = None
    if version == "0.2":
        checker = FormatChecker()
        checker.checks("date-time")(_valid_timestamp)
    validator = Draft202012Validator(
        schema,
        registry=schema_registry(),
        format_checker=checker,
    )
    errors = sorted(validator.iter_errors(document), key=lambda item: item.json_path)
    if errors:
        raise ContractError(
            "\n".join(
                f"{contract}{error.json_path}: {error.message}" for error in errors
            )
        )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _equal(actual: Any, expected: Any, label: str) -> None:
    _require(actual == expected, f"{label} mismatch")


def _subset(actual: list, expected: list, label: str) -> None:
    _require(set(actual) <= set(expected), f"{label} exceeds permitted values")


def _scope(path: str) -> ScopeExpression:
    try:
        return parse_scope(path)
    except ValueError as error:
        raise ContractError(str(error)) from error


def _scope_subset(paths: list[str], parents: list[str], label: str) -> None:
    parent_scopes = [_scope(path) for path in parents]
    for path in paths:
        child = _scope(path)
        _require(
            any(parent.contains(child) for parent in parent_scopes),
            f"{label} exceeds parent scope: {path}",
        )


def _limits(actual: dict, parent: dict, label: str) -> None:
    for key, value in actual.items():
        _require(key in parent and value <= parent[key], f"{label} exceeds {key}")


def content_digest(value: dict) -> str:
    canonical = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()


def _counts(counts: dict) -> None:
    _require(
        {"max_concurrent_agents", "max_total_agent_launches", "max_delegation_depth"}
        <= counts.keys(),
        "Missing agent-count limits",
    )
    _require(
        counts["max_concurrent_agents"] <= counts["max_total_agent_launches"],
        "Concurrent limit exceeds total launch limit",
    )


def _interval(document: dict) -> tuple[datetime, datetime]:
    start = datetime.fromisoformat(document["issued_at"])
    end = datetime.fromisoformat(document["expires_at"])
    _require(start < end, "Validity interval is empty or reversed")
    return start, end


def _observation(observation: dict) -> None:
    if observation["kind"] == "candidate":
        candidate = observation["candidate"]
        for field in ("base_commit", "workspace_fingerprint"):
            _equal(candidate[field], observation[field], f"Candidate {field}")


def validate_bundle(documents: dict[str, dict]) -> None:
    """Check a 0.2 workflow's declared relationships, without live authority checks."""
    _require(isinstance(documents, dict), "Expected a workflow object")
    _require(set(LEGACY_CONTRACTS) <= documents.keys(), "Missing workflow contracts")
    for name, document in documents.items():
        _require(isinstance(document, dict), f"Expected {name} object")
        _equal(document.get("schema_version"), "0.2", "Workflow contract family")
        validate_document(name, document)

    task, context, grant, execution, delivery = (
        documents[name] for name in LEGACY_CONTRACTS
    )
    identity = task["task"]
    revision = task["plan"]["revision"]
    context_revision = context["identity"]["revision"]
    observation = context["observation"]
    units = {unit["id"]: unit for unit in task["plan"]["work_units"]}
    _equal(len(units), len(task["plan"]["work_units"]), "Unique Work Unit IDs")
    _equal(context["identity"]["task_id"], identity["id"], "Context task")
    _equal(
        context["identity"]["repository"], identity["repository"], "Context repository"
    )
    _equal(context_revision["commit"], observation["base_commit"], "Context baseline")
    if context_revision.get("workspace_fingerprint") is not None:
        _equal(
            context_revision["workspace_fingerprint"],
            observation["workspace_fingerprint"],
            "Context fingerprint",
        )
    _observation(observation)
    for name, document in (
        ("Approval", grant),
        ("Execution", execution),
        ("Delivery", delivery),
    ):
        _equal(document["task_id"], identity["id"], f"{name} task")
        _equal(document["plan_revision"], revision, f"{name} plan revision")
    _equal(grant["status"], "active", "Declared approval status")
    _require(grant.get("revoked_at") is None, "Declared approval has been revoked")
    _interval(grant)
    _equal(delivery["repository"], identity["repository"], "Delivery repository")
    _equal(execution["authorization"]["grant_id"], grant["grant_id"], "Execution grant")
    _equal(
        execution["context"]["package_id"], context["package_id"], "Execution context"
    )
    _equal(
        execution["context"]["snapshot_id"],
        context_revision["snapshot_id"],
        "Execution snapshot",
    )
    _equal(execution["observation"], observation, "Execution observation")
    for name, workspace in (
        ("Approval", grant["workspace"]),
        ("Execution", execution["workspace"]),
    ):
        _equal(workspace["repository"], identity["repository"], f"{name} repository")
        _equal(
            workspace["baseline_commit"], observation["base_commit"], f"{name} baseline"
        )
        _equal(workspace["branch"], context_revision["branch"], f"{name} branch")
    _equal(
        execution["workspace"]["workspace_id"],
        grant["workspace"].get("workspace_id"),
        "Workspace identity",
    )
    _equal(
        execution["workspace"]["expected_fingerprint"],
        observation["workspace_fingerprint"],
        "Workspace fingerprint",
    )
    _require(execution["work_unit_id"] in units, "Unknown execution Work Unit")
    unit = units[execution["work_unit_id"]]
    if "candidate" in grant:
        _equal(observation["kind"], "candidate", "Authorized observation kind")
        _equal(grant["candidate"], observation["candidate"], "Authorized observation")
        _require("requirements" in unit, "Missing authorized plan requirements")
        _equal(
            grant["requirements_digest"],
            unit["requirements"]["digest"],
            "Authorized plan requirements",
        )
    _require(
        unit["id"] in grant["scope"].get("work_unit_ids", []),
        "Work Unit outside approval",
    )
    operations = execution["authorization"]["required_operations"]
    _subset(operations, grant["authorization"]["operations"], "Execution operations")
    if task["assessment"]["profile"] == "explore":
        allowed = ["investigate", "review", "delegate"]
        _subset(
            task["approval"]["required_actions"], allowed, "Explore requested actions"
        )
        _subset(grant["authorization"]["operations"], allowed, "Explore authorization")
        _subset(operations, allowed, "Explore execution")
        _require(
            unit.get("commit_required") is False, "Explore Work Unit must be read-only"
        )
    _scope_subset(
        execution["scope"]["allowed_paths"],
        grant["scope"]["allowed_paths"],
        "Execution scope",
    )
    _scope_subset(
        execution["scope"]["allowed_paths"], unit["scope"], "Execution Work Unit scope"
    )
    _subset(
        grant["scope"]["protected_paths"],
        execution["scope"]["protected_paths"],
        "Inherited protected paths",
    )
    if "delegate" in grant["authorization"]["operations"]:
        _counts(task["plan"].get("delegation", {}))
        _counts(grant["authorization"]["delegation"])
        _limits(
            grant["authorization"]["delegation"],
            task["plan"].get("delegation", {}),
            "Grant agent counts",
        )
    if "agent_counts" in execution:
        _limits(
            execution["agent_counts"],
            grant["authorization"].get("delegation", {}),
            "Execution agent counts",
        )

    runtime_names = {"sandbox", "runtime-capability", "runtime-evidence-approval"}
    if runtime_names & documents.keys():
        _require(runtime_names <= documents.keys(), "Incomplete runtime bindings")
        _runtime(documents)
    agent_names = {
        "agent-profile",
        "agent-assignment",
        "child-authority",
        "agent-result",
    }
    if agent_names & documents.keys():
        _require(
            (agent_names - {"agent-result"}) | runtime_names <= documents.keys(),
            "Incomplete assignment bindings",
        )
        _assignment(documents)
    _delivery(documents, units)


def _assignment(documents: dict[str, dict]) -> None:
    task, context, grant, execution = (documents[name] for name in LEGACY_CONTRACTS[:4])
    assignment = documents["agent-assignment"]
    profile = documents["agent-profile"]
    child = documents["child-authority"]
    sandbox = documents["sandbox"]
    _require(
        "delegate" in grant["authorization"]["operations"],
        "Missing explicit delegation permission",
    )
    if task["assessment"]["profile"] == "explore":
        _equal(assignment["access_mode"], "read_only", "Explore assignment mode")
    expected = {
        "task_id": task["task"]["id"],
        "plan_revision": task["plan"]["revision"],
        "work_unit_id": execution["work_unit_id"],
        "context_id": context["package_id"],
        "repository": task["task"]["repository"],
        "observation": context["observation"],
    }
    for name, document in (("Assignment", assignment), ("Child authority", child)):
        for key, value in expected.items():
            _equal(document[key], value, f"{name} {key}")
    _equal(
        assignment["snapshot_id"],
        context["identity"]["revision"]["snapshot_id"],
        "Assignment snapshot",
    )
    for key in ("profile_id", "profile_revision", "role_id", "role_revision"):
        _equal(assignment[key], profile[key], key)
    for key in ("assignment_id", "child_authority_id", "parent_execution_id"):
        _equal(child[key], assignment[key], f"Child {key}")
    for key in (
        "assignment_id",
        "child_authority_id",
        "parent_execution_id",
        "sandbox_id",
        "capability_id",
        "runtime_approval_id",
        "accounting_id",
    ):
        _equal(execution.get(key), assignment[key], f"Execution {key}")
    _equal(child["parent_grant_id"], grant["grant_id"], "Parent grant")
    _equal(child["status"], "active", "Declared child authority status")
    parent_start, parent_end = _interval(grant)
    child_start, child_end = _interval(child)
    _require(
        parent_start <= child_start < child_end <= parent_end,
        "Child validity exceeds parent",
    )
    _subset(
        child["operations"], grant["authorization"]["operations"], "Child operations"
    )
    _subset(child["operations"], profile["capabilities"], "Profile capabilities")
    _require(
        not set(child["operations"]) & set(profile["restrictions"]),
        "Profile restriction violated",
    )
    _subset(assignment["operations"], child["operations"], "Assignment operations")
    _subset(
        execution["authorization"]["required_operations"],
        assignment["operations"],
        "Assigned execution operations",
    )
    _scope_subset(
        child["allowed_paths"], grant["scope"]["allowed_paths"], "Child scope"
    )
    _scope_subset(
        assignment["allowed_paths"], child["allowed_paths"], "Assignment scope"
    )
    _scope_subset(
        execution["scope"]["allowed_paths"],
        assignment["allowed_paths"],
        "Assigned execution scope",
    )
    _subset(
        grant["scope"]["protected_paths"],
        child["protected_paths"],
        "Child protected paths",
    )
    _subset(
        child["protected_paths"],
        assignment["protected_paths"],
        "Assignment protected paths",
    )
    _subset(
        assignment["protected_paths"],
        execution["scope"]["protected_paths"],
        "Execution protected paths",
    )
    _limits(child["agent_counts"], grant["authorization"]["delegation"], "Child counts")
    _limits(assignment["agent_counts"], child["agent_counts"], "Assignment counts")
    _limits(
        execution["agent_counts"],
        assignment["agent_counts"],
        "Assigned execution counts",
    )
    for counts in (
        child["agent_counts"],
        assignment["agent_counts"],
        execution["agent_counts"],
    ):
        _counts(counts)
    _limits(child["budget"], grant["resource_limits"], "Child budget")
    _limits(assignment["budget"], child["budget"], "Assignment budget")
    _limits(
        {key: execution["budget"][key] for key in assignment["budget"]},
        assignment["budget"],
        "Execution budget",
    )
    depth = child["delegation_depth"]
    _require(
        depth <= child["agent_counts"]["max_delegation_depth"],
        "Delegation depth exceeded",
    )
    if "delegate" in child["operations"]:
        _require(
            depth < child["agent_counts"]["max_delegation_depth"],
            "Recursive delegation exceeds depth",
        )
    _equal(
        len({item["label"] for item in assignment["specializations"]}),
        len(assignment["specializations"]),
        "Unique specialization labels",
    )
    _equal(sandbox["sandbox_id"], assignment["sandbox_id"], "Sandbox identity")
    _equal(sandbox["repository"], assignment["repository"], "Sandbox repository")
    _equal(sandbox["observation"], assignment["observation"], "Sandbox observation")
    _scope_subset(
        sandbox["writable_paths"], assignment["allowed_paths"], "Sandbox writable scope"
    )
    if assignment["access_mode"] == "read_only":
        _require(
            not sandbox["writable_paths"]
            and all(mount["read_only"] for mount in sandbox["mounts"]),
            "Read-only assignment has a writable source boundary",
        )
    _equal(
        assignment["runtime_approval_id"],
        sandbox["runtime_approval_id"],
        "Assigned runtime approval",
    )
    _equal(assignment["capability_id"], sandbox["capability_id"], "Assigned capability")
    if "agent-result" in documents:
        result = documents["agent-result"]
        for key in (
            *expected,
            "assignment_id",
            "parent_execution_id",
            "snapshot_id",
            "child_authority_id",
            "access_mode",
        ):
            _equal(result[key], assignment[key], f"Result {key}")
        _changes(
            result["changes"],
            assignment["allowed_paths"],
            assignment["protected_paths"],
        )
        if result["changes"]:
            _require(
                "implement" in assignment["operations"],
                "Changes require implementation permission",
            )
        _subset(
            [item["change_type"] for item in result["changes"]],
            profile["supported_change_types"],
            "Supported changes",
        )
        for finding in result["findings"]:
            _equal(
                finding["observation"], assignment["observation"], "Finding observation"
            )
        _equal(
            len({item["finding_id"] for item in result["findings"]}),
            len(result["findings"]),
            "Unique finding IDs",
        )
        _equal(
            len({item["artifact_id"] for item in result["artifacts"]}),
            len(result["artifacts"]),
            "Unique artifact IDs",
        )
        _equal(
            len({item["path"].casefold() for item in result["artifacts"]}),
            len(result["artifacts"]),
            "Unique artifact paths",
        )
        for artifact in result["artifacts"]:
            path = _scope(artifact["path"])
            _require(
                path.kind == ScopeKind.FILE
                and not _scope(".git/**").matches(path.path.casefold()),
                "Invalid artifact path",
            )


def _runtime(documents: dict[str, dict]) -> None:
    sandbox = documents["sandbox"]
    capability = documents["runtime-capability"]
    approval = documents["runtime-evidence-approval"]
    _equal(
        sandbox["repository"],
        documents["task"]["task"]["repository"],
        "Sandbox repository",
    )
    _equal(
        sandbox["observation"],
        documents["context"]["observation"],
        "Sandbox observation",
    )
    configuration = {
        key: value
        for key, value in sandbox.items()
        if key
        not in (
            "schema_version",
            "sandbox_id",
            "configuration_digest",
            "repository",
            "observation",
            "capability_id",
            "runtime_approval_id",
        )
    }
    _equal(
        sandbox["configuration_digest"],
        content_digest(configuration),
        "Configuration digest",
    )
    _equal(
        capability["digest"],
        content_digest(
            {key: value for key, value in capability.items() if key != "digest"}
        ),
        "Capability content digest",
    )
    for key in (
        "capability_id",
        "configuration_digest",
        "adapter_id",
        "adapter_version",
        "runtime_id",
        "runtime_version",
        "image",
        "environment",
    ):
        _equal(sandbox[key], capability[key], f"Sandbox {key}")
        _equal(approval[key], capability[key], f"Runtime approval {key}")
    _equal(
        sandbox["runtime_approval_id"],
        approval["runtime_approval_id"],
        "Runtime approval identity",
    )
    _equal(approval["capability_digest"], capability["digest"], "Capability digest")
    _equal(approval["status"], "active", "Declared runtime approval status")
    _interval(approval)
    _equal(
        set(approval["evidence_digests"]),
        {item["digest"] for item in capability["evidence_references"]},
        "Approved evidence digests",
    )
    _subset(sandbox["required_controls"], capability["controls"], "Runtime controls")
    _subset(
        [
            "repository_isolation",
            "process_isolation",
            "authority_isolation",
            "context_isolation",
            "resource_limits",
            "descendant_termination",
        ],
        sandbox["required_controls"],
        "Mandatory isolation controls",
    )
    network_control = (
        "network_deny"
        if sandbox["network"]["mode"] == "denied"
        else "network_allowlist"
    )
    _require(
        network_control in sandbox["required_controls"],
        "Missing required network control",
    )


def _changes(files: list[dict], allowed: list[str], protected: list[str]) -> None:
    _equal(
        len({item["path"].casefold() for item in files}),
        len(files),
        "Unique changed paths",
    )
    denials = [_scope(path.casefold()) for path in (".git/**", *protected)]
    for file in files:
        paths = [file["path"]]
        if file.get("previous_path") is not None:
            paths.append(file["previous_path"])
        _scope_subset(paths, allowed, "Changed path")
        for path in paths:
            _require(
                not any(rule.matches(path.casefold()) for rule in denials),
                "Changed path is protected",
            )


def _delivery(documents: dict[str, dict], units: dict[str, dict]) -> None:
    delivery, execution, grant = (
        documents[name] for name in ("delivery", "execution", "approval")
    )
    seen = set()
    _require(
        len(delivery["work_units"]) <= 1,
        "Bundle validation requires one Work Unit cohort",
    )
    for operation, outcome in delivery["publication"].items():
        if outcome["status"] in ("authorized", "executed"):
            _require(
                operation in grant["authorization"]["operations"],
                "Publication permission is missing",
            )
            _equal(outcome.get("grant_id"), grant["grant_id"], "Publication grant")
    manifest = delivery.get("candidate_manifest")
    if manifest:
        context = documents["context"]
        _equal(context["observation"]["kind"], "candidate", "Candidate context kind")
        _equal(
            manifest["candidate"],
            context["observation"]["candidate"],
            "Manifest candidate",
        )
        _equal(manifest["repository"], delivery["repository"], "Manifest repository")
        _equal(
            manifest["snapshot_id"],
            context["identity"]["revision"]["snapshot_id"],
            "Manifest snapshot",
        )
        candidate_payload = {
            key: value for key, value in manifest.items() if key != "candidate"
        }
        candidate_payload["base_commit"] = manifest["candidate"]["base_commit"]
        candidate_payload["workspace_fingerprint"] = manifest["candidate"][
            "workspace_fingerprint"
        ]
        _equal(
            manifest["candidate"]["digest"],
            content_digest(candidate_payload),
            "Candidate manifest digest",
        )
        _require("agent-result" in documents, "Missing result lineage record")
        _equal(
            manifest["result_package_ids"],
            [documents["agent-result"]["result_id"]],
            "Supported result lineage",
        )
        dispositions = {item["result_id"]: item for item in manifest["contributions"]}
        _equal(
            len(dispositions),
            len(manifest["contributions"]),
            "Unique contribution dispositions",
        )
        _equal(
            {
                key
                for key, value in dispositions.items()
                if value["disposition"] == "accepted"
            },
            set(manifest["result_package_ids"]),
            "Accepted contribution lineage",
        )
        if manifest["files"] != documents["agent-result"]["changes"]:
            _require(
                bool(manifest["resolution_references"]),
                "Missing integration resolution record",
            )
        _changes(
            manifest["files"],
            execution["scope"]["allowed_paths"],
            execution["scope"]["protected_paths"],
        )
    for unit in delivery["work_units"]:
        identifier = unit["work_unit_id"]
        _require(
            identifier in units and identifier not in seen,
            "Unknown or duplicate delivered Work Unit",
        )
        seen.add(identifier)
        _equal(identifier, execution["work_unit_id"], "Delivered execution Work Unit")
        _equal(
            unit["change_boundary"]["base_commit"],
            execution["observation"]["base_commit"],
            "Delivery baseline",
        )
        _changes(
            unit["change_boundary"]["files"],
            units[identifier]["scope"],
            execution["scope"]["protected_paths"],
        )
        if "candidate" not in unit:
            _require(not manifest, "Missing Work Unit candidate")
            if unit["status"] == "findings_ready":
                results = {item["check_id"]: item for item in unit["verification"]}
                _equal(
                    len(results), len(unit["verification"]), "Unique read-only checks"
                )
                for check in execution["verification"]["required_checks"]:
                    if check["required"]:
                        _require(
                            check["id"] in results
                            and results[check["id"]]["status"] == "passed",
                            "Required read-only verification is incomplete",
                        )
            continue
        _require(manifest is not None, "Missing candidate manifest")
        _equal(unit["candidate"], manifest["candidate"], "Delivery candidate")
        _equal(
            unit["change_boundary"]["files"],
            manifest["files"],
            "Final candidate file boundary",
        )
        _equal(
            unit["change_boundary"]["workspace_fingerprint"],
            unit["candidate"]["workspace_fingerprint"],
            "Delivery fingerprint",
        )
        _equal(unit["requirements"], manifest["requirements"], "Candidate requirements")
        _equal(
            unit["requirements"],
            units[identifier].get("requirements"),
            "Recorded plan requirements",
        )
        requirements = unit["requirements"]
        _equal(
            requirements["digest"],
            content_digest(
                {key: value for key, value in requirements.items() if key != "digest"}
            ),
            "Requirements digest",
        )
        required_checks = {
            item["id"]
            for item in execution["verification"]["required_checks"]
            if item["required"]
        }
        _equal(
            set(requirements["required_checks"]),
            required_checks,
            "Execution verification requirements",
        )
        checks, reviews = {}, {}
        for field, records, identity in (
            ("verification", checks, "check_id"),
            ("reviews", reviews, "review_id"),
        ):
            for item in unit[field]:
                _require(item[identity] not in records, f"Duplicate {identity}")
                records[item[identity]] = item
                _equal(item["candidate"], unit["candidate"], f"{field} candidate")
                _equal(
                    item["requirements_digest"],
                    unit["requirements"]["digest"],
                    f"{field} requirements",
                )
                if field == "verification":
                    _equal(
                        item["execution_id"],
                        execution["execution_id"],
                        "Verification execution",
                    )
                    _require(
                        "runtime-evidence-approval" in documents,
                        "Missing verification runtime approval",
                    )
                    _equal(
                        item["runtime_approval_id"],
                        documents["runtime-evidence-approval"]["runtime_approval_id"],
                        "Verification runtime approval",
                    )
        application = unit.get("application", {})
        if (
            application.get("status") == "applied"
            or unit["status"]
            in ("commit_proposed", "awaiting_commit", "committed", "findings_ready")
            or delivery["pull_request"]["status"] in ("proposed", "open", "merged")
        ):
            required = unit["requirements"]
            _require(
                all(
                    check in checks and checks[check]["status"] == "passed"
                    for check in required["required_checks"]
                ),
                "Required candidate verification is incomplete",
            )
            _require(
                all(
                    review in reviews and reviews[review]["outcome"] == "accepted"
                    for review in required["required_review_ids"]
                ),
                "Required candidate review is incomplete",
            )
            if required["human_review_required"]:
                _require(
                    any(
                        item["outcome"] == "accepted"
                        and item["reviewer_kind"] == "human"
                        for item in reviews.values()
                    ),
                    "Required human review is incomplete",
                )
        if "candidate" in application:
            _equal(application["candidate"], unit["candidate"], "Applied candidate")
        if application.get("status") == "applied":
            _equal(application["grant_id"], grant["grant_id"], "Application grant")
            _require(
                "apply_candidate" in grant["authorization"]["operations"],
                "Missing candidate application permission",
            )
        if "application_gate" in execution:
            gate = execution["application_gate"]
            _equal(gate["candidate"], unit["candidate"], "Application gate candidate")
            _equal(
                gate["requirements_digest"],
                requirements["digest"],
                "Application gate requirements",
            )
            _equal(
                set(gate["verification_ids"]),
                {item["evidence_id"] for item in checks.values()},
                "Application gate evidence",
            )
            _equal(set(gate["review_ids"]), set(reviews), "Application gate reviews")
        if "candidate" in grant:
            _equal(grant["candidate"], unit["candidate"], "Authorized candidate")
            _equal(
                grant["requirements_digest"],
                unit["requirements"]["digest"],
                "Authorized requirements",
            )
    _subset(
        delivery["pull_request"].get("included_work_units", []),
        list(seen),
        "PR Work Units",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    document = commands.add_parser("document")
    document.add_argument("contract", choices=EXTENSION_CONTRACTS)
    document.add_argument("path", type=Path)
    bundle = commands.add_parser("bundle")
    bundle.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        value = load_json(args.path)
        if args.command == "document":
            validate_document(args.contract, value)
        else:
            validate_bundle(value)
    except (ContractError, OSError, ValueError) as error:
        parser.exit(1, f"Validation failed: {error}\n")
    print(
        "Structure validated"
        if args.command == "document"
        else "Structure and declared bindings validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
