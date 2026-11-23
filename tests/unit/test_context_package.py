import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

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
