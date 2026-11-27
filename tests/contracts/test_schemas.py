"""
AEW JSON Schema contract validation.

Validates:
- Every contract schema against JSON Schema Draft 2020-12.
- Positive fixtures must pass validation.
- Negative fixtures must fail validation.
- Every schema must have at least one positive fixture.

Fixture naming:
    contracts/examples/task.quick.json
    contracts/examples/task.invalid-missing-objective.json

Negative fixtures must contain ".invalid-" in their name.

Run:
    python -m pytest tests/contracts/test_schemas.py -v

Dependencies:
    pytest
    jsonschema
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from contracts.validation import EXTENSION_CONTRACTS, schema_registry

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONTRACTS_DIR = PROJECT_ROOT / "contracts"
EXAMPLES_DIR = CONTRACTS_DIR / "examples"

SCHEMA_FILES = (
    "task.schema.json",
    "context.schema.json",
    "approval.schema.json",
    "execution.schema.json",
    "delivery.schema.json",
)

SCHEMA_PATHS = tuple(CONTRACTS_DIR / filename for filename in SCHEMA_FILES) + tuple(
    CONTRACTS_DIR / "v0.2" / f"{name}.schema.json" for name in EXTENSION_CONTRACTS
)
ALL_SCHEMA_PATHS = (*SCHEMA_PATHS, CONTRACTS_DIR / "v0.2/common.schema.json")


def load_json(path: Path) -> Any:
    """Load JSON without silently accepting duplicate keys."""

    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON property: {key}")

            result[key] = value

        return result

    with path.open("r", encoding="utf-8") as file:
        return json.load(
            file,
            object_pairs_hook=reject_duplicates,
        )


def schema_name(path: Path) -> str:
    """Extract the contract name from its filename."""
    return path.name.removesuffix(".schema.json")


def discover_fixtures(
    contract: str,
    *,
    invalid: bool,
    directory: Path = EXAMPLES_DIR,
) -> list[Path]:
    """Discover fixtures for a particular contract."""

    if not directory.is_dir():
        return []

    fixtures = sorted(directory.glob(f"{contract}.*.json"))

    if invalid:
        return [path for path in fixtures if ".invalid-" in path.name]

    return [path for path in fixtures if ".invalid-" not in path.name]


@pytest.mark.parametrize(
    "schema_path",
    ALL_SCHEMA_PATHS,
    ids=lambda path: f"{path.parent.name}/{path.name}",
)
def test_schema_is_valid(schema_path: Path) -> None:
    """Each schema must be a valid Draft 2020-12 schema."""

    assert schema_path.is_file(), f"Missing contract schema: {schema_path}"

    schema = load_json(schema_path)

    assert schema.get("$schema") == ("https://json-schema.org/draft/2020-12/schema")

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        pytest.fail(f"Invalid schema {schema_path.name}: {error}")


@pytest.mark.parametrize(
    "schema_path",
    SCHEMA_PATHS,
    ids=lambda path: path.name,
)
def test_positive_fixtures(schema_path: Path) -> None:
    """Every contract needs valid example coverage."""

    assert schema_path.is_file(), f"Missing contract schema: {schema_path}"

    contract = schema_name(schema_path)

    fixtures = discover_fixtures(
        contract,
        invalid=False,
        directory=schema_path.parent / "examples",
    )

    assert fixtures, (
        f"No positive fixtures found for {contract}. "
        f"Add contracts/examples/{contract}.<name>.json"
    )

    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, registry=schema_registry())

    for fixture_path in fixtures:
        instance = load_json(fixture_path)

        errors = sorted(
            validator.iter_errors(instance),
            key=lambda error: (
                tuple(str(part) for part in error.path),
                error.message,
            ),
        )

        assert not errors, (
            f"Positive fixture failed: {fixture_path.name}\n"
            + "\n".join(f"- {error.json_path}: {error.message}" for error in errors)
        )


@pytest.mark.parametrize(
    "schema_path",
    SCHEMA_PATHS,
    ids=lambda path: path.name,
)
def test_negative_fixtures(schema_path: Path) -> None:
    """Negative fixtures must be rejected by their schema."""

    assert schema_path.is_file(), f"Missing contract schema: {schema_path}"

    contract = schema_name(schema_path)

    fixtures = discover_fixtures(
        contract,
        invalid=True,
        directory=schema_path.parent / "examples",
    )

    if not fixtures:
        assert schema_path.parent == CONTRACTS_DIR, (
            "Every 0.2 contract needs negative fixtures"
        )
        pytest.skip(f"No negative fixtures defined for {contract}")

    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, registry=schema_registry())

    for fixture_path in fixtures:
        instance = load_json(fixture_path)

        errors = list(validator.iter_errors(instance))

        assert errors, f"Negative fixture unexpectedly passed: {fixture_path.name}"


def test_schema_identifiers_are_unique() -> None:
    """Contract schema identifiers must not collide."""

    identifiers: set[str] = set()

    for schema_path in ALL_SCHEMA_PATHS:
        assert schema_path.is_file()

        schema = load_json(schema_path)
        identifier = schema.get("$id")

        assert isinstance(identifier, str)
        assert identifier

        assert identifier not in identifiers, (
            f"Duplicate schema identifier: {identifier}"
        )

        identifiers.add(identifier)


def test_fixture_names_reference_known_contracts() -> None:
    """Fixture files must belong to a known contract."""

    if not EXAMPLES_DIR.is_dir():
        return

    for directory in (CONTRACTS_DIR, CONTRACTS_DIR / "v0.2"):
        known_contracts = {
            schema_name(path) for path in SCHEMA_PATHS if path.parent == directory
        }
        for fixture_path in (directory / "examples").glob("*.json"):
            contract = fixture_path.name.split(".", 1)[0]
            assert contract in known_contracts, (
                f"Unknown contract fixture: {fixture_path.name}"
            )
