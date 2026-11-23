"""Prepare one commit proposal from a recorded Work Unit and isolated change review."""

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from engine.delivery.verification import (
    DeliveryError,
    VerificationStatus,
    resolve_checks,
)
from engine.execution.changes import ChangeReview
from engine.execution.checkpoint import CheckpointStore
from engine.execution.envelope import ExecutionEnvelope
from engine.git.preflight import parse_scope
from engine.git.repository import GitRepository
from engine.planning.history import PlanRevision


@dataclass(frozen=True)
class UnitDelivery:
    envelope: ExecutionEnvelope
    review: ChangeReview
    title: str
    summary: str
    evidence_ids: tuple[str, ...] = ()
    omissions: tuple[tuple[str, VerificationStatus, str], ...] = ()
    risks: tuple[str, ...] = ()


def propose_commit(
    repository: GitRepository,
    store: CheckpointStore,
    revision: PlanRevision,
    unit: UnitDelivery,
) -> dict[str, Any]:
    record = revision.to_record()
    task = record["task_document"]["task"]
    envelope, review = unit.envelope, unit.review
    planned = next(
        (
            item
            for item in record["boundaries"]["work_units"]
            if item["id"] == envelope.work_unit_id
        ),
        None,
    )
    if (
        planned is None
        or not planned["commit_required"]
        or (envelope.task_id, envelope.workspace.repository, envelope.plan_revision)
        != (task["id"], task["repository"], revision.revision)
        or envelope.context_id != record["boundaries"]["context_package"]
        or envelope.workspace.repository != repository.root.as_uri()
        or review.commit != envelope.workspace.commit
    ):
        raise DeliveryError(
            "Commit proposal does not match a deliverable Work Unit and its bindings"
        )
    if (
        not unit.title.strip()
        or any(char in unit.title for char in "\r\n")
        or not unit.summary.strip()
    ):
        raise DeliveryError(
            "Commit proposal requires a single-line title and a change summary"
        )
    digest = review.verified_digest()
    if not review.replacements or not review.diff:
        raise DeliveryError("Commit proposal requires reviewed changes")
    scope = tuple(parse_scope(path) for path in planned["scope"])
    allowed = tuple(parse_scope(path) for path in envelope.allowed_paths)
    files = []
    paths = set()
    for change in review.replacements:
        if change.path in paths or not all(
            any(rule.matches(change.path) for rule in rules)
            for rules in (scope, allowed)
        ):
            raise DeliveryError(
                "Reviewed file is duplicated or outside the Work Unit boundary"
            )
        paths.add(change.path)
        files.append(
            {
                "path": change.path,
                "change_type": "added" if change.expected_oid is None else "modified",
                "before_hash": f"git:{change.expected_oid}"
                if change.expected_oid is not None
                else None,
                "after_hash": "sha256:" + sha256(change.content.encode()).hexdigest(),
            }
        )
    verification = resolve_checks(
        store,
        task_id=task["id"],
        plan_revision=revision.revision,
        work_unit_id=envelope.work_unit_id,
        repository=task["repository"],
        commit=review.commit,
        review_digest=digest,
        execution_id=envelope.execution_id,
        required=tuple(planned["verification"]),
        evidence_ids=unit.evidence_ids,
        omissions=unit.omissions,
    )
    snapshot = repository.snapshot()
    staged = [
        item.path for item in snapshot.changes if item.index_status not in (" ", "?")
    ]
    unstaged = [item.path for item in snapshot.changes if item.worktree_status != " "]
    risks = list(unit.risks)
    if staged:
        risks.append("Excluded staged paths: " + ", ".join(staged))
    if unstaged:
        risks.append("Excluded unstaged or untracked paths: " + ", ".join(unstaged))
    if (
        snapshot.head_commit != review.commit
        or snapshot.branch != envelope.workspace.branch
    ):
        risks.append("The shared checkout differs from the reviewed baseline.")
    checks_pass = bool(verification) and all(
        item.status == VerificationStatus.PASSED for item in verification
    )
    references = [f"#{task['issue_number']}"] if "issue_number" in task else []
    body = [unit.summary, "", "Verification:"]
    body.extend(
        f"- {item.check}: {item.status.value}"
        + (f" ({item.reason})" if item.reason else "")
        for item in verification
    )
    if risks:
        body.extend(["", "Review notes:", *(f"- {risk}" for risk in risks)])
    body.extend(f"\nRefs {reference}" for reference in references)
    return {
        "work_unit_id": envelope.work_unit_id,
        "status": "commit_proposed" if checks_pass else "not_ready",
        "commit_proposal": {
            "title": unit.title,
            "body": "\n".join(body),
            "format": "custom",
            "references": references,
        },
        "change_boundary": {
            "base_commit": review.commit,
            "files": sorted(files, key=lambda item: item["path"]),
            "separation": "isolated_patch",
            "workspace_fingerprint": envelope.fingerprint,
            "patch_reference": f"sha256:{digest}",
        },
        "verification": [item.to_document() for item in verification],
    }
