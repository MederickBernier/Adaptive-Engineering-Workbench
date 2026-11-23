"""Trusted host handoff from advisory task plans to guarded AEW tools."""

from typing import Any

from engine.context.package import ContextPackage
from engine.delivery.draft import prepare_delivery, review_progress
from engine.delivery.proposal import UnitDelivery
from engine.execution.authority import ExecutionDenied, GrantVerifier, SignedGrant
from engine.execution.changes import TextReplacement
from engine.execution.checkpoint import CheckpointStore
from engine.execution.controller import ExecutionController, ReadEvidence
from engine.execution.envelope import ExecutionEnvelope, ExecutionPolicy
from engine.execution.isolated import CheckResult, DockerSandbox, IsolatedChecks
from engine.git.preflight import parse_scope
from engine.git.repository import GitRepository
from engine.planning.history import PlanHistory, plan_id


class TaskHost:
    """Trusted integration boundary. Expose only individual mediated operations."""

    def __init__(
        self,
        repository: GitRepository,
        history: PlanHistory,
        verifier: GrantVerifier,
        checkpoints: CheckpointStore,
        *,
        protected_paths: tuple[str, ...] = (),
        sandbox: DockerSandbox | None = None,
        allowed_checks: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        self._repository = repository
        self._history = history
        self._verifier = verifier
        self._checkpoints = checkpoints
        policy = ExecutionPolicy(
            repository, history, verifier, protected_paths=protected_paths
        )
        self._reader = ExecutionController(repository, policy, checkpoints)
        self._runner = (
            IsolatedChecks(
                repository, policy, checkpoints, sandbox, allowed_checks or {}
            )
            if sandbox is not None
            else None
        )

    def _plan(self, task_id: str, revision: int) -> dict[str, Any]:
        identifier = plan_id(self._repository.root.as_uri(), task_id)
        if self._history.latest_revision(identifier) != revision:
            raise ExecutionDenied("Workflow plan revision is unknown or superseded")
        record = self._history.load(identifier, revision).to_record()
        return record

    def _isolation_gate(self, task_id: str, revision: int) -> None:
        record = self._plan(task_id, revision)
        document = record["task_document"]
        if document["assessment"]["profile"] == "explore":
            raise ExecutionDenied(
                "Explore plans are limited to read-only investigation"
            )
        if document.get("preflight", {}).get("status") not in ("passed", "warning"):
            raise ExecutionDenied(
                "Resolve mandatory preflight evidence before isolated implementation"
            )
        inspected = tuple(
            parse_scope(item)
            for item in record["boundaries"]["repository_observation"]["scope"]
        )
        if any(
            not any(parent.contains(parse_scope(item)) for parent in inspected)
            for item in record["boundaries"]["scope"]
        ):
            raise ExecutionDenied(
                "Recorded preflight does not cover the full plan scope"
            )

    def read(
        self,
        envelope: ExecutionEnvelope,
        context: ContextPackage,
        signed: SignedGrant,
        *,
        path: str,
        expected_oid: str,
    ) -> ReadEvidence:
        self._plan(envelope.task_id, envelope.plan_revision)
        return self._reader.read(
            envelope, context, signed, path=path, expected_oid=expected_oid
        )

    def resume_read(
        self, envelope: ExecutionEnvelope, context: ContextPackage, signed: SignedGrant
    ) -> None:
        self._plan(envelope.task_id, envelope.plan_revision)
        self._reader.resume(envelope, context, signed)

    def verify(
        self,
        envelope: ExecutionEnvelope,
        context: ContextPackage,
        signed: SignedGrant,
        *,
        replacements: tuple[TextReplacement, ...],
        check: str,
    ) -> CheckResult:
        self._isolation_gate(envelope.task_id, envelope.plan_revision)
        if self._runner is None:
            raise ExecutionDenied(
                "The trusted isolated execution runner is unavailable"
            )
        return self._runner.run(
            envelope, context, signed, replacements=replacements, name=check
        )

    def resume_verification(
        self,
        envelope: ExecutionEnvelope,
        context: ContextPackage,
        signed: SignedGrant,
        *,
        replacements: tuple[TextReplacement, ...],
        check: str,
    ) -> None:
        self._isolation_gate(envelope.task_id, envelope.plan_revision)
        if self._runner is None:
            raise ExecutionDenied(
                "The trusted isolated execution runner is unavailable"
            )
        self._runner.resume(
            envelope, context, signed, replacements=replacements, name=check
        )

    def draft(
        self,
        *,
        task_id: str,
        revision: int,
        units: tuple[UnitDelivery, ...],
        base_branch: str,
        head_branch: str,
    ) -> dict[str, Any]:
        self._isolation_gate(task_id, revision)
        return prepare_delivery(
            self._repository,
            self._history,
            self._checkpoints,
            task_id=task_id,
            revision=revision,
            units=units,
            base_branch=base_branch,
            head_branch=head_branch,
        )

    def review(
        self,
        *,
        task_id: str,
        revision: int,
        units: tuple[UnitDelivery, ...],
        base_branch: str,
        head_branch: str,
        reviews: tuple[SignedGrant, ...],
    ) -> tuple[tuple[str, ...], str | None]:
        self._isolation_gate(task_id, revision)
        return review_progress(
            self._repository,
            self._history,
            self._checkpoints,
            self._verifier,
            task_id=task_id,
            revision=revision,
            units=units,
            base_branch=base_branch,
            head_branch=head_branch,
            reviews=reviews,
        )
