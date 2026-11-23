import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from engine.context.expansion import expand_context
from engine.context.package import ContextPackage, ContextPackageError

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"


@pytest.fixture
def content() -> dict:
    document = json.loads((CONTRACTS / "examples" / "context.basic.json").read_bytes())
    del document["package_id"]
    return document


def test_sealed_context_round_trips_and_validates_against_contract(
    content: dict,
) -> None:
    package = ContextPackage.create(content)
    schema = json.loads((CONTRACTS / "context.schema.json").read_bytes())
    Draft202012Validator(schema).validate(package.to_dict())
    noncanonical = json.dumps(package.to_dict(), indent=4, ensure_ascii=False)
    assert ContextPackage.from_json(noncanonical) == package
    reordered = dict(reversed(tuple(content.items())))
    assert ContextPackage.create(reordered).package_id == package.package_id


def test_input_documents_and_returned_copies_cannot_modify_package(
    content: dict,
) -> None:
    package = ContextPackage.create(content)
    original = package.to_json()
    content["integrity"]["limitations"].clear()
    exported = package.to_dict()
    exported["identity"]["revision"]["snapshot_id"] = "replacement"

    assert package.to_json() == original
    assert ContextPackage.create(content).package_id != package.package_id


@pytest.mark.parametrize(
    "section", ["identity", "integrity", "project", "knowledge", "parent"]
)
def test_load_rejects_tampered_content(content: dict, section: str) -> None:
    changed = ContextPackage.create(content).to_dict()
    if section == "parent":
        changed["parent_package_id"] = "other-package"
    else:
        changed[section]["edited"] = True
    with pytest.raises(ContextPackageError, match="digest"):
        ContextPackage.from_json(json.dumps(changed))


def test_load_rejects_duplicate_keys_and_missing_digest(content: dict) -> None:
    package = ContextPackage.create(content)
    duplicate = b'{"schema_version":"0.1",' + package.to_json()[1:]
    with pytest.raises(ContextPackageError, match="Duplicate"):
        ContextPackage.from_json(duplicate)
    with pytest.raises(ContextPackageError, match="digest"):
        ContextPackage.from_json(json.dumps(content))


def test_sealing_rejects_incomplete_revision_and_nonfinite_json(content: dict) -> None:
    invalid = {**content, "identity": {"task_id": "test", "repository": "example/api"}}
    with pytest.raises(ContextPackageError, match="revision binding"):
        ContextPackage.create(invalid)
    with pytest.raises(ContextPackageError, match="finite JSON"):
        ContextPackage.create({**content, "bad_number": float("nan")})


def additional_context(content: dict) -> ContextPackage:
    added = {
        **content["knowledge"]["assertions"][0],
        "id": "assertion.extra",
        "claim": "Additional evidence is available.",
        "verification": "stale",
    }
    return ContextPackage.create(
        {
            "schema_version": "0.1",
            "identity": content["identity"],
            "integrity": {
                "freshness": "stale",
                "coverage": "partial",
                "limitations": ["Extra evidence is historical."],
                "discovery_depth": "light",
            },
            "knowledge": {"assertions": [added]},
        }
    )


def test_expansion_creates_linked_valid_package_and_preserves_evidence(
    content: dict,
) -> None:
    parent = ContextPackage.create(content)
    original = parent.to_json()
    additional = additional_context(content)

    expanded = expand_context(parent, additional)
    document = expanded.to_dict()
    schema = json.loads((CONTRACTS / "context.schema.json").read_bytes())
    Draft202012Validator(schema).validate(document)
    assert document["parent_package_id"] == parent.package_id
    assert expanded.package_id not in (parent.package_id, additional.package_id)
    assert document["knowledge"]["assertions"] == (
        content["knowledge"]["assertions"]
        + additional.to_dict()["knowledge"]["assertions"]
    )
    assert document["integrity"]["freshness"] == "stale"
    assert "Extra evidence is historical." in document["integrity"]["limitations"]
    assert expanded == ContextPackage.from_json(expanded.to_json())
    assert parent.to_json() == original


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("identity", "task_id", "task-elsewhere"),
        ("identity", "repository", "example/other"),
        ("revision", "commit", "b" * 40),
        ("revision", "branch", "next"),
        ("revision", "snapshot_id", "another-snapshot"),
        ("revision", "workspace_fingerprint", "another-workspace"),
    ],
)
def test_expansion_rejects_incompatible_bindings(
    content: dict, section: str, field: str, value: str
) -> None:
    parent = ContextPackage.create(content)
    candidate = additional_context(content).to_dict()
    del candidate["package_id"]
    target = (
        candidate["identity"]
        if section == "identity"
        else candidate["identity"]["revision"]
    )
    target[field] = value
    with pytest.raises(ContextPackageError, match="same task, repository"):
        expand_context(parent, ContextPackage.create(candidate))


def test_expansion_rejects_budget_loss_and_no_op(content: dict) -> None:
    parent = ContextPackage.create(content)
    with pytest.raises(ContextPackageError, match="preserve all evidence"):
        expand_context(
            parent, additional_context(content), max_bytes=len(parent.to_json())
        )
    with pytest.raises(ContextPackageError, match="adds no new"):
        expand_context(parent, parent)


def test_expansion_rejects_conflicting_evidence_for_an_assertion_id(
    content: dict,
) -> None:
    parent = ContextPackage.create(content)
    candidate = parent.to_dict()
    del candidate["package_id"]
    candidate["knowledge"]["assertions"][0]["evidence"][0]["reference"] = (
        "conflicting.py"
    )
    with pytest.raises(ContextPackageError, match="Conflicting evidence"):
        expand_context(parent, ContextPackage.create(candidate))
