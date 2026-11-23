"""Append-only plan revisions in the local Project Brain database."""

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from engine.brain.store import ProjectBrain
from engine.planning.assessment import PlanningError
from engine.planning.plan import PlanDraft


class PlanConflict(PlanningError):
    """The expected plan revision has been superseded."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def plan_id(repository: str, task_id: str) -> str:
    return "plan-" + sha256(_json([repository, task_id]).encode("utf-8")).hexdigest()


def _repository_observation(draft: PlanDraft) -> dict[str, Any] | None:
    report = draft.preflight
    if report is None:
        return None
    baseline = report.baseline
    return {
        "head": report.head_commit,
        "branch": report.branch,
        "integration_branch": report.integration_branch,
        "tracking_commit": report.integration_commit,
        "remote_commit": baseline.remote_commit if baseline else None,
        "remote": baseline.remote if baseline else None,
        "status": report.status.value,
        "scope": sorted(report.intended_scope),
        "workspace": report.workspace.state.value,
        "overlap": report.workspace.overlap.value,
        "changed_paths": sorted(report.workspace.changed_paths),
        "proposed_branch": report.proposed_branch,
        "branch_collision": report.branch_collision,
        "pull_requests_checked": report.pull_requests_checked,
        "pull_requests": [[pr.number, pr.head_commit] for pr in report.pull_requests],
        "findings": [
            [item.code, item.severity.value, list(item.evidence)]
            for item in report.findings
        ],
    }


def _material(draft: PlanDraft, document: dict[str, Any]) -> dict[str, Any]:
    task = document["task"]
    return {
        "objective": task["objective"],
        "acceptance_criteria": task["acceptance_criteria"],
        "task_constraints": task["constraints"],
        "issue": task.get("issue_number"),
        "planning_profile": draft.assessment.profile.value,
        "risk_and_uncertainty": [
            draft.assessment.risk.value,
            draft.assessment.uncertainty.value,
        ],
        "evidence": list(draft.assessment.evidence),
        "approach": draft.approach,
        "scope": sorted(draft.scope),
        "work_units": [
            {**unit.to_document(), "verification": list(unit.verification)}
            for unit in draft.work_units
        ],
        "verification": document["plan"]["verification"],
        "approval_checkpoints": [
            asdict(checkpoint) for checkpoint in draft.checkpoints
        ],
        "review_questions": list(draft.review_questions),
        "assumptions": list(draft.assumptions),
        "investigation_budget": draft.investigation_budget,
        "context_package": draft.context.package_id if draft.context else None,
        "repository_observation": _repository_observation(draft),
    }


@dataclass(frozen=True)
class PlanRevision:
    plan_id: str
    revision: int
    recorded_at: str
    material_changes: tuple[str, ...]
    _payload: str

    @property
    def previous_revision(self) -> int | None:
        return self.revision - 1 if self.revision > 1 else None

    @property
    def approval_reassessment_required(self) -> bool:
        return self.previous_revision is not None and bool(self.material_changes)

    def to_record(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "revision": self.revision,
            "previous_revision": self.previous_revision,
            "recorded_at": self.recorded_at,
            "material_changes": list(self.material_changes),
            "approval_reassessment_required": self.approval_reassessment_required,
            **json.loads(self._payload),
        }


class PlanHistory:
    """Persist immutable plan revisions, serialized by an expected predecessor."""

    def __init__(self, brain: ProjectBrain) -> None:
        self._brain = brain

    def append(self, draft: PlanDraft, *, expected_revision: int = 0) -> PlanRevision:
        """Append a draft or return the existing revision for an identical retry."""
        if draft.task.repository != self._brain.repository:
            raise PlanningError("Plan repository does not match the Project Brain")
        if type(expected_revision) is not int or expected_revision < 0:
            raise PlanningError("Expected revision must be a nonnegative integer")
        identifier = plan_id(draft.task.repository, draft.task.id)
        with closing(sqlite3.connect(self._brain.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            latest = db.execute(
                "SELECT revision, recorded_at, material, payload, changes FROM plan_revisions "
                "WHERE plan_id = ? ORDER BY revision DESC LIMIT 1",
                (identifier,),
            ).fetchone()
            current = latest[0] if latest else 0
            document = draft.to_task_document(revision=max(current, 1))
            material = _json(_material(draft, document))
            payload = {
                "task_document": document,
                "recommended_profile": draft.assessment.recommended.value,
                "boundaries": json.loads(material),
            }
            if (
                latest
                and expected_revision in (current - 1, current)
                and _json(payload) == latest[3]
            ):
                return PlanRevision(
                    identifier,
                    current,
                    latest[1],
                    tuple(json.loads(latest[4])),
                    latest[3],
                )
            if current != expected_revision:
                raise PlanConflict(
                    f"Expected plan revision {expected_revision}, found {current}"
                )
            previous = json.loads(latest[2]) if latest else {}
            values = payload["boundaries"]
            changes = tuple(
                sorted(
                    key for key in values if latest and values[key] != previous.get(key)
                )
            )
            revision = current + 1
            document["plan"]["revision"] = revision
            recorded = datetime.now(UTC).isoformat()
            serialized = _json(payload)
            db.execute(
                "INSERT INTO plan_revisions VALUES (?, ?, ?, ?, ?, ?)",
                (identifier, revision, recorded, material, serialized, _json(changes)),
            )
            return PlanRevision(identifier, revision, recorded, changes, serialized)

    def load(self, identifier: str, revision: int) -> PlanRevision:
        """Read the requested revision without substituting a newer plan."""
        with closing(sqlite3.connect(self._brain.path)) as db:
            row = db.execute(
                "SELECT recorded_at, payload, changes FROM plan_revisions "
                "WHERE plan_id = ? AND revision = ?",
                (identifier, revision),
            ).fetchone()
        if row is None:
            raise KeyError((identifier, revision))
        return PlanRevision(
            identifier, revision, row[0], tuple(json.loads(row[2])), row[1]
        )
