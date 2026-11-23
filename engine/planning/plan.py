"""Validated advisory plans and Work Units for the v0.1 Task contract."""

from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from typing import Any

from engine.context.package import ContextPackage
from engine.git.preflight import (
    LocalPreflightReport,
    OverlapStatus,
    ScopeExpression,
    ScopeSyntaxError,
    parse_scope,
)
from engine.git.repository import WorkspaceState
from engine.planning.assessment import Assessment, PlanningError, Profile


def _scopes(scope: tuple[str, ...]) -> tuple[ScopeExpression, ...]:
    try:
        return tuple(parse_scope(item) for item in scope)
    except ScopeSyntaxError as error:
        raise PlanningError(f"Invalid planning scope: {error}") from error


@dataclass(frozen=True)
class Task:
    id: str
    repository: str
    objective: str
    acceptance: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    title: str | None = None
    issue_number: int | None = None

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.id, self.repository, self.objective)
        ):
            raise PlanningError("Task ID, repository, and objective are required")
        if self.issue_number is not None and (
            type(self.issue_number) is not int or self.issue_number < 1
        ):
            raise PlanningError("Issue number must be a positive integer")

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": "local" if self.issue_number is None else "github",
            "repository": self.repository,
            "objective": self.objective,
            "acceptance_criteria": list(self.acceptance),
            "constraints": list(self.constraints),
            **({"title": self.title} if self.title is not None else {}),
            **(
                {"issue_number": self.issue_number}
                if self.issue_number is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class WorkUnit:
    id: str
    objective: str
    scope: tuple[str, ...]
    acceptance: tuple[str, ...]
    verification: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    commit_required: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.objective.strip():
            raise PlanningError("Work Unit ID and objective are required")
        if (
            not self.acceptance
            or not self.verification
            or not all(
                value.strip() for value in (*self.acceptance, *self.verification)
            )
        ):
            raise PlanningError(
                "Each Work Unit needs acceptance criteria and verification"
            )
        if len(set(self.dependencies)) != len(self.dependencies):
            raise PlanningError("Duplicate Work Unit dependency")

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "objective": self.objective,
            "scope": list(self.scope),
            "acceptance": list(self.acceptance),
            "dependencies": list(self.dependencies),
            "commit_required": self.commit_required,
        }


@dataclass(frozen=True)
class ApprovalCheckpoint:
    action: str
    event: str
    work_unit_id: str | None = None
    scope: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanDraft:
    task: Task
    assessment: Assessment
    approach: str
    scope: tuple[str, ...]
    work_units: tuple[WorkUnit, ...]
    verification: tuple[str, ...]
    checkpoints: tuple[ApprovalCheckpoint, ...]
    review_questions: tuple[str, ...]
    assumptions: tuple[str, ...]
    context: ContextPackage | None
    preflight: LocalPreflightReport | None
    investigation_budget: int | None

    def to_task_document(self, *, revision: int = 1) -> dict[str, Any]:
        """Export the versioned task document. Checkpoints describe approval needs."""
        if type(revision) is not int or revision < 1:
            raise PlanningError("Plan revision must be a positive integer")
        return {
            "schema_version": "0.1",
            "task": self.task.to_document(),
            "assessment": {
                "profile": self.assessment.profile.value,
                "rationale": self.assessment.rationale,
                "risk": self.assessment.risk.value,
                "uncertainty": self.assessment.uncertainty.value,
            },
            "evidence": [
                {"reference": item, "verification": "provisional"}
                for item in self.assessment.evidence
            ]
            + (
                [
                    {
                        "reference": self.context.package_id,
                        "verification": "verified",
                        "description": "Context Package digest verified; claim verification is recorded in the package.",
                    }
                ]
                if self.context
                else []
            ),
            "plan": {
                "revision": revision,
                "approach": self.approach,
                "scope": list(self.scope),
                "work_units": [unit.to_document() for unit in self.work_units],
                "verification": list(
                    dict.fromkeys(
                        (
                            *self.verification,
                            *(
                                check
                                for unit in self.work_units
                                for check in unit.verification
                            ),
                        )
                    )
                ),
            },
            "approval": {
                "status": "pending" if self.checkpoints else "not_requested",
                "required_actions": list(
                    dict.fromkeys(checkpoint.action for checkpoint in self.checkpoints)
                ),
                "questions": list(self.review_questions),
            },
            **(
                {"preflight": _preflight_document(self.preflight)}
                if self.preflight
                else {}
            ),
        }


def _preflight_document(report: LocalPreflightReport) -> dict[str, Any]:
    workspace = "unknown"
    if report.workspace.state == WorkspaceState.CLEAN:
        workspace = "clean"
    elif report.workspace.overlap == OverlapStatus.OVERLAPPING:
        workspace = "dirty_overlapping"
    elif report.workspace.overlap == OverlapStatus.NON_OVERLAPPING:
        workspace = "dirty_non_overlapping"
    return {
        "status": report.status.value,
        "branch": report.branch or "",
        "commit": report.head_commit or "",
        "workspace": workspace,
        "relevant_prs": [pr.number for pr in report.pull_requests],
        "findings": [f"{item.code}: {item.message}" for item in report.findings],
        **(
            {"proposed_branch": report.proposed_branch}
            if report.proposed_branch
            else {}
        ),
    }


def _ordered_units(
    units: tuple[WorkUnit, ...], scope: tuple[str, ...]
) -> tuple[WorkUnit, ...]:
    parents = _scopes(scope)
    by_id = {unit.id: unit for unit in units}
    if len(by_id) != len(units):
        raise PlanningError("Duplicate Work Unit ID")
    for unit in units:
        if set(unit.dependencies) - by_id.keys():
            raise PlanningError(f"Unknown Work Unit dependency for {unit.id}")
        if any(
            not any(parent.contains(child) for parent in parents)
            for child in _scopes(unit.scope)
        ):
            raise PlanningError(f"Work Unit scope exceeds the plan: {unit.id}")
    try:
        order = TopologicalSorter(
            {unit.id: unit.dependencies for unit in units}
        ).static_order()
        return tuple(by_id[unit_id] for unit_id in order)
    except CycleError as error:
        raise PlanningError("Work Unit dependencies contain a cycle") from error


def build_plan(
    task: Task,
    assessment: Assessment,
    *,
    approach: str,
    scope: tuple[str, ...] = (),
    verification: tuple[str, ...] = (),
    work_units: tuple[WorkUnit, ...] = (),
    context: ContextPackage | None = None,
    preflight: LocalPreflightReport | None = None,
    review_questions: tuple[str, ...] = (),
    assumptions: tuple[str, ...] = (),
    create_branch: bool = False,
    investigation_budget: int | None = None,
) -> PlanDraft:
    """Validate an advisory plan without requesting or issuing grants."""
    if not approach.strip():
        raise PlanningError("A plan requires an approach")
    identity = context.to_dict()["identity"] if context else None
    if identity and (identity["task_id"], identity["repository"]) != (
        task.id,
        task.repository,
    ):
        raise PlanningError("Context Package belongs to a different task or repository")
    review = list(review_questions)
    explore = assessment.profile == Profile.EXPLORE
    plan_scope = _scopes(scope)
    if preflight is not None:
        if preflight.repository.as_uri() != task.repository:
            raise PlanningError("Preflight belongs to a different repository")
        if identity and (
            identity["revision"]["commit"] != preflight.head_commit
            or identity["revision"]["branch"] != preflight.branch
        ):
            raise PlanningError("Context and preflight revisions are incompatible")
        if not explore and preflight.status.value in ("blocked", "unavailable"):
            review.append(
                f"Resolve preflight status {preflight.status.value} before restricted implementation."
            )
        inspected = _scopes(preflight.intended_scope)
        if any(
            not any(parent.contains(child) for parent in inspected)
            for child in plan_scope
        ):
            review.append("Obtain preflight evidence for the full plan scope.")
    elif not explore:
        review.append("Obtain repository preflight before restricted implementation.")
    if context is None and not explore:
        review.append(
            "Review relevant Context Package evidence before restricted implementation."
        )
    elif (
        context is not None
        and context.to_dict()["integrity"].get("freshness") != "current"
    ):
        review.append(
            "Review the freshness and applicability of Context Package claims."
        )

    if explore:
        if create_branch or any(unit.commit_required for unit in work_units):
            raise PlanningError(
                "Explore units cannot propose commits or branch creation"
            )
        if type(investigation_budget) is not int or investigation_budget < 1:
            raise PlanningError("Explore requires a positive investigation budget")
        if not review_questions or not task.acceptance or not verification:
            raise PlanningError(
                "Explore requires investigation questions, expected outcomes, and stopping checks"
            )
    else:
        if investigation_budget is not None:
            raise PlanningError("An investigation budget applies to Explore planning")
        if not scope or not task.acceptance:
            raise PlanningError(
                "Implementation planning requires scope and task acceptance criteria"
            )
        if not work_units and assessment.profile == Profile.QUICK:
            work_units = (
                WorkUnit(
                    f"{task.id}-01",
                    task.objective,
                    scope,
                    task.acceptance,
                    verification,
                ),
            )
        if not work_units or any(not unit.scope for unit in work_units):
            raise PlanningError("Implementation planning requires scoped Work Units")

    ordered = _ordered_units(work_units, scope)
    checkpoints: list[ApprovalCheckpoint] = []
    if create_branch:
        checkpoints.append(
            ApprovalCheckpoint("create_branch", "before_branch_creation")
        )
    if explore:
        checkpoints.append(
            ApprovalCheckpoint(
                "investigate", "before_restricted_investigation", scope=scope
            )
        )
    else:
        for unit in ordered:
            checkpoints.extend(
                (
                    ApprovalCheckpoint(
                        "implement",
                        "before_restricted_implementation",
                        unit.id,
                        unit.scope,
                    ),
                    ApprovalCheckpoint(
                        "run_tests",
                        "before_restricted_verification",
                        unit.id,
                        unit.scope,
                    ),
                )
            )
    return PlanDraft(
        task,
        assessment,
        approach,
        scope,
        ordered,
        verification,
        tuple(checkpoints),
        tuple(dict.fromkeys(review)),
        assumptions,
        context,
        preflight,
        investigation_budget,
    )
