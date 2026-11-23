from pathlib import Path

import pytest

from engine.delivery.verification import (
    DeliveryError,
    VerificationStatus,
    resolve_checks,
)
from engine.execution.authority import WorkspaceBinding
from engine.execution.checkpoint import CheckpointStore
from engine.execution.envelope import ExecutionBudget, ExecutionEnvelope


def test_verification_requires_observed_boundary_specific_evidence(
    tmp_path: Path,
) -> None:
    store = CheckpointStore(tmp_path / "checks.sqlite3")
    workspace = WorkspaceBinding("example/project", "master", "a" * 40, "checkout")
    envelope = ExecutionEnvelope(
        "execution-1",
        "task",
        1,
        "unit",
        "context",
        "snapshot",
        "grant",
        workspace,
        "fingerprint",
        ("run_tests",),
        ("src/**",),
        ExecutionBudget(2, 2, 30),
    )

    def run(name, code):
        pending = store.reserve(envelope, "@isolated-check", name)
        return store.finish(
            envelope,
            pending,
            success=True,
            observed_check=(name, code, "review", "image"),
        ).evidence_id

    passing, failing = run("tests", 0), run("lint", 1)
    options = {
        "task_id": "task",
        "plan_revision": 1,
        "work_unit_id": "unit",
        "repository": workspace.repository,
        "commit": workspace.commit,
        "review_digest": "review",
        "execution_id": envelope.execution_id,
        "required": ("tests", "lint", "smoke", "external", "review"),
        "evidence_ids": (passing, failing),
        "omissions": (
            ("smoke", VerificationStatus.SKIPPED, "Deferred"),
            ("external", VerificationStatus.UNAVAILABLE, "No provider"),
        ),
    }
    results = resolve_checks(CheckpointStore(tmp_path / "checks.sqlite3"), **options)
    assert [result.status for result in results] == list(VerificationStatus)
    assert [result.to_document()["status"] for result in results] == [
        "passed",
        "failed",
        "incomplete",
        "incomplete",
        "not_run",
    ]
    with pytest.raises(DeliveryError, match="was not observed"):
        resolve_checks(store, **(options | {"evidence_ids": ("forged",)}))
    with pytest.raises(DeliveryError, match="does not match"):
        resolve_checks(store, **(options | {"review_digest": "other"}))
