"""Read-only delivery preparation and signed sequential review checkpoints."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from engine.delivery.proposal import UnitDelivery, propose_commit
from engine.delivery.verification import DeliveryError
from engine.execution.authority import GrantVerifier, SignedGrant
from engine.execution.checkpoint import CheckpointStore
from engine.execution.envelope import observe_workspace
from engine.git.preflight import parse_scope
from engine.git.repository import GitRepository
from engine.planning.history import PlanHistory, plan_id


def _digest(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(canonical).hexdigest()


def review_digest(document: dict[str, Any], work_unit_id: str) -> str:
    unit = next(
        (
            item
            for item in document["work_units"]
            if item["work_unit_id"] == work_unit_id
        ),
        None,
    )
    if unit is None:
        raise DeliveryError("Unknown Work Unit review")
    proposal = {key: value for key, value in unit.items() if key != "status"}
    return _digest(
        [
            document["task_id"],
            document["repository"],
            document["plan_revision"],
            proposal,
        ]
    )


def prepare_delivery(
    repository: GitRepository,
    history: PlanHistory,
    checks: CheckpointStore,
    *,
    task_id: str,
    revision: int,
    units: tuple[UnitDelivery, ...],
    base_branch: str,
    head_branch: str,
) -> dict[str, Any]:
    """Prepare a v0.1 delivery document without Git or GitHub writes."""
    identity = repository.root.as_uri()
    identifier = plan_id(identity, task_id)
    if history.latest_revision(identifier) != revision:
        raise DeliveryError("Delivery requires the current recorded plan revision")
    if base_branch == head_branch or not all(
        repository.is_valid_branch_name(name) for name in (base_branch, head_branch)
    ):
        raise DeliveryError("A PR draft requires distinct valid base and head branches")
    plan = history.load(identifier, revision)
    record = plan.to_record()
    deliverable = [
        item["id"]
        for item in record["boundaries"]["work_units"]
        if item["commit_required"]
    ]
    by_id = {item.envelope.work_unit_id: item for item in units}
    if not units or len(by_id) != len(units) or set(by_id) - set(deliverable):
        raise DeliveryError(
            "Supply unique reviewed edits for recorded deliverable Work Units"
        )
    if set(by_id) != set(deliverable[: len(units)]):
        raise DeliveryError(
            "Work Unit proposals must follow the recorded sequential order"
        )
    proposals = [
        propose_commit(repository, checks, plan, by_id[item])
        for item in deliverable
        if item in by_id
    ]
    task = record["task_document"]["task"]
    title = task.get("title") or task["objective"]
    body = ["## Summary", "", task["objective"], "", "## Work Units", ""]
    for unit in proposals:
        body.extend(
            [
                f"### {unit['work_unit_id']}",
                "",
                unit["commit_proposal"]["body"],
                "",
            ]
        )
    missing = [item for item in deliverable if item not in by_id]
    if missing:
        body.extend(
            ["## Pending Work Units", "", *(f"- {item}" for item in missing), ""]
        )
    if "issue_number" in task:
        body.extend(["## Related issue", "", f"Refs #{task['issue_number']}"])
    document = {
        "schema_version": "0.1",
        "task_id": task_id,
        "repository": identity,
        "plan_revision": revision,
        "work_units": proposals,
        "pull_request": {
            "status": "proposed"
            if not missing
            and all(item["status"] == "commit_proposed" for item in proposals)
            else "not_ready",
            "title": " ".join(title.splitlines()),
            "body": "\n".join(body).rstrip(),
            "base_branch": base_branch,
            "head_branch": head_branch,
            "included_work_units": [item["work_unit_id"] for item in proposals],
        },
        "publication": {
            operation: {"status": "not_authorized"}
            for operation in ("stage", "commit", "push", "create_pr", "merge")
        },
    }
    return {**document, "delivery_id": "delivery-" + _digest(document)}


def review_progress(
    repository: GitRepository,
    history: PlanHistory,
    checks: CheckpointStore,
    verifier: GrantVerifier,
    *,
    task_id: str,
    revision: int,
    units: tuple[UnitDelivery, ...],
    base_branch: str,
    head_branch: str,
    reviews: tuple[SignedGrant, ...],
) -> tuple[tuple[str, ...], str | None]:
    """Recognize only an ordered prefix of exact, separately signed human reviews."""
    document = prepare_delivery(
        repository,
        history,
        checks,
        task_id=task_id,
        revision=revision,
        units=units,
        base_branch=base_branch,
        head_branch=head_branch,
    )
    if len(reviews) > len(units):
        raise DeliveryError("More reviews than Work Unit proposals")
    workspace, fingerprint = observe_workspace(repository) if reviews else (None, None)
    accepted = []
    proposals = document["work_units"]
    for signed, proposal in zip(reviews, proposals, strict=False):
        work_unit = proposal["work_unit_id"]
        grant = verifier.verify(signed, now=datetime.now(UTC))
        boundary = proposal["change_boundary"]
        if (
            grant.review_digest != review_digest(document, work_unit)
            or grant.task_id != task_id
            or grant.plan_revision != revision
            or grant.workspace != workspace
            or boundary["workspace_fingerprint"] != fingerprint
            or boundary["base_commit"] != grant.workspace.commit
            or grant.work_units != (work_unit,)
            or "commit" not in grant.operations
            or proposal["status"] != "commit_proposed"
        ):
            raise DeliveryError(
                "Review does not authorize this exact sequential checkpoint"
            )
        allowed = tuple(parse_scope(path) for path in grant.allowed_paths)
        protected = tuple(
            parse_scope(path.casefold()) for path in (".git/**", *grant.protected_paths)
        )
        if any(
            not any(rule.matches(file["path"]) for rule in allowed)
            or any(rule.matches(file["path"].casefold()) for rule in protected)
            for file in boundary["files"]
        ):
            raise DeliveryError("Review scope does not cover the proposed changes")
        accepted.append(work_unit)
    identifier = plan_id(document["repository"], task_id)
    record = history.load(identifier, revision).to_record()
    order = [
        item["id"]
        for item in record["boundaries"]["work_units"]
        if item["commit_required"]
    ]
    return tuple(accepted), order[len(accepted)] if len(accepted) < len(order) else None
