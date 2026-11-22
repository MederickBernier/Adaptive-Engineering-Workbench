"""
AEW cross-contract semantic validation tests.

Purpose:
    Validate relationships and invariants between
    Task, Context, Approval, Execution, and Delivery
    contracts.

These tests are independent of the AEW engine.

Run:
    python -m pytest tests/contracts/test_semantics.py -v

Dependencies:
    pytest
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "contracts" / "examples"


def load_fixture(name: str) -> dict[str, Any]:
    """Load a positive contract fixture."""

    path = EXAMPLES / name

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def task() -> dict[str, Any]:
    return load_fixture("task.quick.json")


@pytest.fixture
def context() -> dict[str, Any]:
    return load_fixture("context.basic.json")


@pytest.fixture
def approval() -> dict[str, Any]:
    return load_fixture("approval.basic.json")


@pytest.fixture
def execution() -> dict[str, Any]:
    return load_fixture("execution.basic.json")


@pytest.fixture
def delivery() -> dict[str, Any]:
    return load_fixture("delivery.basic.json")


def work_unit_ids(task: dict[str, Any]) -> set[str]:
    """Collect declared Work Unit identifiers."""

    return {unit["id"] for unit in task["plan"]["work_units"]}


def validate_task_context(
    task: dict[str, Any],
    context: dict[str, Any],
) -> list[str]:
    """Validate task and context identity consistency."""

    errors: list[str] = []

    if context["identity"]["task_id"] != task["task"]["id"]:
        errors.append("Context task identity mismatch")

    if context["identity"]["repository"] != task["task"]["repository"]:
        errors.append("Context repository mismatch")

    return errors


def validate_task_approval(
    task: dict[str, Any],
    approval: dict[str, Any],
) -> list[str]:
    """Validate approval references to task and plan."""

    errors: list[str] = []

    if approval["task_id"] != task["task"]["id"]:
        errors.append("Approval task identity mismatch")

    if approval["plan_revision"] != task["plan"]["revision"]:
        errors.append("Approval plan revision mismatch")

    known_units = work_unit_ids(task)

    for unit_id in approval["scope"].get("work_unit_ids", []):
        if unit_id not in known_units:
            errors.append(f"Unknown approved Work Unit: {unit_id}")

    return errors


def validate_execution_bindings(
    task: dict[str, Any],
    context: dict[str, Any],
    approval: dict[str, Any],
    execution: dict[str, Any],
) -> list[str]:
    """Validate execution references and requested scope."""

    errors: list[str] = []

    if execution["task_id"] != task["task"]["id"]:
        errors.append("Execution task identity mismatch")

    if execution["work_unit_id"] not in work_unit_ids(task):
        errors.append("Execution references unknown Work Unit")

    if execution["plan_revision"] != task["plan"]["revision"]:
        errors.append("Execution plan revision mismatch")

    if execution["authorization"]["grant_id"] != approval["grant_id"]:
        errors.append("Execution approval grant mismatch")

    if execution["context"]["package_id"] != context["package_id"]:
        errors.append("Execution context package mismatch")

    if (
        execution["context"]["snapshot_id"]
        != context["identity"]["revision"]["snapshot_id"]
    ):
        errors.append("Execution snapshot mismatch")

    if execution["workspace"]["repository"] != approval["workspace"]["repository"]:
        errors.append("Execution repository mismatch")

    if execution["workspace"]["branch"] != approval["workspace"]["branch"]:
        errors.append("Execution branch mismatch")

    if (
        execution["workspace"]["baseline_commit"]
        != approval["workspace"]["baseline_commit"]
    ):
        errors.append("Execution baseline mismatch")

    if (
        execution["workspace"]["baseline_commit"]
        != context["identity"]["revision"]["commit"]
    ):
        errors.append("Execution and context revision mismatch")

    if execution["workspace"]["workspace_id"] != approval["workspace"].get(
        "workspace_id"
    ):
        errors.append("Execution workspace identity mismatch")

    requested = set(execution["authorization"]["required_operations"])

    permitted = set(approval["authorization"]["operations"])

    unauthorized = requested - permitted

    if unauthorized:
        errors.append(
            "Unauthorized operations requested: " + ", ".join(sorted(unauthorized))
        )

    if approval["status"] != "active":
        errors.append("Approval grant is not active")

    approved_units = set(approval["scope"].get("work_unit_ids", []))

    if approved_units and execution["work_unit_id"] not in approved_units:
        errors.append("Work Unit outside approval scope")

    return errors


def validate_delivery_references(
    task: dict[str, Any],
    delivery: dict[str, Any],
) -> list[str]:
    """Validate delivery identity and Work Unit references."""

    errors: list[str] = []

    if delivery["task_id"] != task["task"]["id"]:
        errors.append("Delivery task identity mismatch")

    if delivery["repository"] != task["task"]["repository"]:
        errors.append("Delivery repository mismatch")

    if delivery["plan_revision"] != task["plan"]["revision"]:
        errors.append("Delivery plan revision mismatch")

    known_units = work_unit_ids(task)

    delivered_units = [unit["work_unit_id"] for unit in delivery["work_units"]]

    for unit_id in delivered_units:
        if unit_id not in known_units:
            errors.append(f"Delivery references unknown Work Unit: {unit_id}")

    if len(delivered_units) != len(set(delivered_units)):
        errors.append("Duplicate Work Unit delivery")

    for unit_id in delivery["pull_request"].get("included_work_units", []):
        if unit_id not in delivered_units:
            errors.append(f"PR references undelivered Work Unit: {unit_id}")

    return errors


def validate_scope_subset(
    approved_paths: list[str],
    execution_paths: list[str],
) -> list[str]:
    """
    Validate exact path membership only.

    Glob patterns and protected-path semantics require
    a dedicated path policy implementation.

    This helper intentionally does not pretend that
    string equality is complete filesystem enforcement.
    """

    approved = set(approved_paths)

    return [
        f"Execution path not explicitly approved: {path}"
        for path in execution_paths
        if path not in approved
    ]


def test_positive_task_context(
    task: dict[str, Any],
    context: dict[str, Any],
) -> None:
    assert validate_task_context(task, context) == []


def test_positive_task_approval(
    task: dict[str, Any],
    approval: dict[str, Any],
) -> None:
    assert validate_task_approval(task, approval) == []


def test_positive_execution_bindings(
    task: dict[str, Any],
    context: dict[str, Any],
    approval: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    assert (
        validate_execution_bindings(
            task,
            context,
            approval,
            execution,
        )
        == []
    )


def test_positive_delivery_references(
    task: dict[str, Any],
    delivery: dict[str, Any],
) -> None:
    assert (
        validate_delivery_references(
            task,
            delivery,
        )
        == []
    )


@pytest.mark.parametrize(
    ("field", "invalid_value", "expected_error"),
    [
        (
            "task_id",
            "github:example/api#999",
            "Execution task identity mismatch",
        ),
        (
            "work_unit_id",
            "unknown-unit",
            "Execution references unknown Work Unit",
        ),
        (
            "plan_revision",
            99,
            "Execution plan revision mismatch",
        ),
    ],
)
def test_invalid_execution_identity(
    task: dict[str, Any],
    context: dict[str, Any],
    approval: dict[str, Any],
    execution: dict[str, Any],
    field: str,
    invalid_value: Any,
    expected_error: str,
) -> None:
    mutated = copy.deepcopy(execution)
    mutated[field] = invalid_value

    errors = validate_execution_bindings(
        task,
        context,
        approval,
        mutated,
    )

    assert expected_error in errors


def test_execution_cannot_expand_operations(
    task: dict[str, Any],
    context: dict[str, Any],
    approval: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    mutated = copy.deepcopy(execution)

    mutated["authorization"]["required_operations"] = [
        "investigate",
        "implement",
        "commit",
    ]

    errors = validate_execution_bindings(
        task,
        context,
        approval,
        mutated,
    )

    assert any(
        error.startswith("Unauthorized operations requested:") for error in errors
    )


def test_revoked_grant_is_not_usable(
    task: dict[str, Any],
    context: dict[str, Any],
    approval: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    mutated = copy.deepcopy(approval)
    mutated["status"] = "revoked"

    errors = validate_execution_bindings(
        task,
        context,
        mutated,
        execution,
    )

    assert "Approval grant is not active" in errors


def test_context_snapshot_mismatch(
    task: dict[str, Any],
    context: dict[str, Any],
    approval: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    mutated = copy.deepcopy(execution)

    mutated["context"]["snapshot_id"] = "wrong-snapshot"

    errors = validate_execution_bindings(
        task,
        context,
        approval,
        mutated,
    )

    assert "Execution snapshot mismatch" in errors


def test_unknown_delivery_work_unit(
    task: dict[str, Any],
    delivery: dict[str, Any],
) -> None:
    mutated = copy.deepcopy(delivery)

    mutated["work_units"][0]["work_unit_id"] = "unknown"

    errors = validate_delivery_references(
        task,
        mutated,
    )

    assert "Delivery references unknown Work Unit: unknown" in errors


def test_duplicate_delivery_work_unit(
    task: dict[str, Any],
    delivery: dict[str, Any],
) -> None:
    mutated = copy.deepcopy(delivery)

    mutated["work_units"].append(copy.deepcopy(mutated["work_units"][0]))

    errors = validate_delivery_references(
        task,
        mutated,
    )

    assert "Duplicate Work Unit delivery" in errors


def test_execution_scope_cannot_expand_exact_paths() -> None:
    approved = [
        "src/customer/CustomerMapper.java",
    ]

    requested = [
        "src/customer/CustomerMapper.java",
        "src/admin/AdminService.java",
    ]

    errors = validate_scope_subset(
        approved,
        requested,
    )

    assert errors == [
        "Execution path not explicitly approved: src/admin/AdminService.java"
    ]
