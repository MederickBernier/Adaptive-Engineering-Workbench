"""Read-only task intake through a persisted advisory plan."""

from dataclasses import dataclass

from engine.brain.discovery import discover
from engine.brain.store import ProjectBrain
from engine.config import load_config
from engine.context.assembly import assemble_context
from engine.context.package import ContextPackage
from engine.git.preflight import GitPreflight, PreflightStatus
from engine.git.repository import GitRepository, WorkspaceState
from engine.github.client import GitHubClient
from engine.planning.assessment import Assessment, PlanningError, Profile
from engine.planning.history import PlanHistory, PlanRevision
from engine.planning.plan import Task, WorkUnit, build_plan


@dataclass(frozen=True)
class Intake:
    task: Task
    assessment: Assessment
    approach: str
    task_type: str
    region: str
    scope: tuple[str, ...]
    verification: tuple[str, ...]
    work_units: tuple[WorkUnit, ...] = ()
    questions: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    investigation_budget: int | None = None
    snapshot_id: str | None = None
    expected_revision: int = 0


@dataclass(frozen=True)
class IntakeResult:
    context: ContextPackage
    revision: PlanRevision
    state: str


def plan_task(
    repository: GitRepository,
    brain: ProjectBrain,
    request: Intake,
    *,
    github: GitHubClient | None = None,
    verify_remote: bool = False,
) -> IntakeResult:
    if (
        request.task.repository != repository.root.as_uri()
        or brain.repository != request.task.repository
    ):
        raise PlanningError("Task and Project Brain must match the selected checkout")
    issue = (
        str(request.task.issue_number) if request.task.issue_number else request.task.id
    )
    report = GitPreflight(
        repository, load_config(repository.root), github=github
    ).inspect(
        task_type=request.task_type,
        issue=issue,
        title=request.task.title or request.task.objective,
        intended_scope=request.scope,
        verify_remote=verify_remote,
    )
    if not report.branch or not report.head_commit:
        raise PlanningError("Task intake requires an attached branch with a commit")
    snapshot_id = (
        request.snapshot_id
        or brain.reconciled_snapshot_id(report.head_commit, request.region)
        or brain.bootstrap_snapshot_id(report.head_commit)
    )
    if snapshot_id is None:
        snapshot_id = discover(
            repository,
            brain,
            commit=report.head_commit,
            regions=(request.region,),
        ).id
    context = assemble_context(
        repository,
        brain,
        snapshot_id,
        task_id=request.task.id,
        branch=report.branch,
        commit=report.head_commit,
        region=request.region,
        preflight=report if report.workspace.state == WorkspaceState.CLEAN else None,
    )
    draft = build_plan(
        request.task,
        request.assessment,
        approach=request.approach,
        scope=request.scope,
        verification=request.verification,
        work_units=request.work_units,
        context=context,
        preflight=report,
        review_questions=request.questions,
        assumptions=request.assumptions,
        investigation_budget=request.investigation_budget,
    )
    if (
        repository.head_commit() != report.head_commit
        or repository.current_branch() != report.branch
    ):
        raise PlanningError("Repository changed during task intake")
    revision = PlanHistory(brain).append(
        draft, expected_revision=request.expected_revision
    )
    state = "awaiting_approval"
    if request.assessment.profile != Profile.EXPLORE and report.status in (
        PreflightStatus.BLOCKED,
        PreflightStatus.UNAVAILABLE,
    ):
        state = "preflight_unresolved"
    return IntakeResult(context, revision, state)
