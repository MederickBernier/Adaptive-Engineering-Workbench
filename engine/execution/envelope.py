"""Bind an execution request to trusted plan, grant, context, and workspace state."""

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from engine.context.package import ContextPackage
from engine.execution.authority import (
    ExecutionDenied,
    GrantVerifier,
    SignedGrant,
    WorkspaceBinding,
)
from engine.git.preflight import ScopeKind, parse_scope
from engine.git.repository import GitRepository, WorkspaceState
from engine.planning.history import PlanHistory, plan_id


@dataclass(frozen=True)
class ExecutionBudget:
    max_iterations: int
    max_tool_calls: int
    max_duration_seconds: int

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value < 1
            for value in (
                self.max_iterations,
                self.max_tool_calls,
                self.max_duration_seconds,
            )
        ):
            raise ValueError("Execution budgets require positive integer limits")


@dataclass(frozen=True)
class ExecutionEnvelope:
    execution_id: str
    task_id: str
    plan_revision: int
    work_unit_id: str
    context_id: str
    snapshot_id: str
    grant_id: str
    workspace: WorkspaceBinding
    fingerprint: str
    operations: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    budget: ExecutionBudget

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.execution_id,
                self.task_id,
                self.work_unit_id,
                self.context_id,
                self.snapshot_id,
                self.grant_id,
                self.fingerprint,
            )
        ):
            raise ValueError("Execution identity and bindings are required")
        if type(self.plan_revision) is not int or self.plan_revision < 1:
            raise ValueError("An envelope requires a positive plan revision")
        if not self.operations or any(
            type(items) is not tuple or any(type(item) is not str for item in items)
            for items in (self.operations, self.allowed_paths)
        ):
            raise ValueError(
                "Envelope operations and paths must be immutable string tuples"
            )
        for path in self.allowed_paths:
            parse_scope(path)


def observe_workspace(repository: GitRepository) -> tuple[WorkspaceBinding, str]:
    """Observe a clean checkout for the committed-content execution adapter."""
    snapshot = repository.snapshot()
    if (
        snapshot.branch is None
        or snapshot.head_commit is None
        or snapshot.workspace_state != WorkspaceState.CLEAN
    ):
        raise ExecutionDenied("This adapter requires a clean, attached checkout")
    binding = WorkspaceBinding(
        snapshot.root.as_uri(),
        snapshot.branch,
        snapshot.head_commit,
        snapshot.git_directory.as_uri(),
    )
    fingerprint = sha256(
        f"{binding.repository}\x00{binding.branch}\x00{binding.commit}\x00{binding.workspace_id}".encode()
    ).hexdigest()
    return binding, fingerprint


class ExecutionPolicy:
    """Check supported requests before the adapter can inspect committed content."""

    def __init__(
        self,
        repository: GitRepository,
        history: PlanHistory,
        verifier: GrantVerifier,
        *,
        protected_paths: tuple[str, ...] = (),
    ) -> None:
        self._repository = repository
        self._history = history
        self._verifier = verifier
        self._protected = tuple(
            parse_scope(path.casefold()) for path in (".git/**", *protected_paths)
        )

    def authorize(
        self,
        envelope: ExecutionEnvelope,
        context: ContextPackage,
        signed: SignedGrant,
        *,
        operation: str,
        path: str,
    ) -> None:
        grant = self._verifier.verify(signed, now=datetime.now(UTC))
        if (
            grant.grant_id != envelope.grant_id
            or grant.task_id != envelope.task_id
            or grant.plan_revision != envelope.plan_revision
            or grant.workspace != envelope.workspace
            or envelope.work_unit_id not in grant.work_units
            or set(envelope.operations) - set(grant.operations)
            or operation not in envelope.operations
        ):
            raise ExecutionDenied("Execution envelope exceeds the signed grant")
        if operation != "investigate":
            raise ExecutionDenied("Operation has no supported guarded adapter")

        observed, fingerprint = observe_workspace(self._repository)
        if observed != envelope.workspace or fingerprint != envelope.fingerprint:
            raise ExecutionDenied("Workspace or baseline changed")
        document = context.to_dict()
        identity = document["identity"]
        revision = identity["revision"]
        if (
            context.package_id != envelope.context_id
            or identity["task_id"] != envelope.task_id
            or identity["repository"] != observed.repository
            or revision["branch"] != observed.branch
            or revision["commit"] != observed.commit
            or revision["snapshot_id"] != envelope.snapshot_id
            or revision.get("workspace_fingerprint") not in (None, fingerprint)
            or document["integrity"].get("freshness") != "current"
        ):
            raise ExecutionDenied(
                "Context binding or freshness could not be established"
            )

        identifier = plan_id(observed.repository, envelope.task_id)
        if self._history.latest_revision(identifier) != envelope.plan_revision:
            raise ExecutionDenied(
                "Execution plan revision is unavailable or superseded"
            )
        record = self._history.load(identifier, envelope.plan_revision).to_record()
        task_document = record["task_document"]
        unit = next(
            (
                item
                for item in task_document["plan"]["work_units"]
                if item["id"] == envelope.work_unit_id
            ),
            None,
        )
        checkpoints = record["boundaries"]["approval_checkpoints"]
        if (
            unit is None
            or record["boundaries"]["context_package"] != envelope.context_id
            or not any(
                checkpoint["action"] == operation
                and checkpoint["work_unit_id"] in (None, envelope.work_unit_id)
                for checkpoint in checkpoints
            )
        ):
            raise ExecutionDenied(
                "Work Unit or Context Package is outside the recorded plan"
            )

        candidate = parse_scope(path)
        if candidate.kind != ScopeKind.FILE:
            raise ExecutionDenied("Investigation requires one exact file path")
        protected = (
            *self._protected,
            *(parse_scope(path.casefold()) for path in grant.protected_paths),
        )
        if any(rule.matches(candidate.path.casefold()) for rule in protected):
            raise ExecutionDenied("The path is protected")
        scopes = tuple(
            tuple(parse_scope(item) for item in scope)
            for scope in (grant.allowed_paths, tuple(unit["scope"]))
        )
        for expression in envelope.allowed_paths:
            if not all(
                any(parent.contains(parse_scope(expression)) for parent in scope)
                for scope in scopes
            ):
                raise ExecutionDenied(
                    "Execution scope expands beyond the grant or Work Unit"
                )
        if not any(
            parse_scope(rule).matches(candidate.path) for rule in envelope.allowed_paths
        ):
            raise ExecutionDenied("The path is outside the execution scope")
