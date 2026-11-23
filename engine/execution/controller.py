"""Budgeted access to explicitly authorized, committed file versions."""

import re
from dataclasses import dataclass

from engine.context.package import ContextPackage
from engine.execution.authority import ExecutionDenied, SignedGrant
from engine.execution.checkpoint import CheckpointStore
from engine.execution.envelope import ExecutionEnvelope, ExecutionPolicy
from engine.git.repository import GitRepository, GitTreeFile


@dataclass(frozen=True)
class ReadEvidence:
    commit: str
    path: str
    oid: str
    content: str


class ExecutionController:
    """Expose a single mediated read tool. The host controls access to other tools."""

    def __init__(
        self,
        repository: GitRepository,
        policy: ExecutionPolicy,
        checkpoints: CheckpointStore,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._checkpoints = checkpoints

    def _file(
        self, envelope: ExecutionEnvelope, path: str, expected_oid: str
    ) -> GitTreeFile:
        matches = self._repository.committed_files(envelope.workspace.commit, path)
        for file in matches:
            if file.path == path and file.oid == expected_oid:
                return file
        raise ExecutionDenied("The exact committed file version could not be verified")

    def read(
        self,
        envelope: ExecutionEnvelope,
        context: ContextPackage,
        signed: SignedGrant,
        *,
        path: str,
        expected_oid: str,
    ) -> ReadEvidence:
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected_oid):
            raise ExecutionDenied("An exact expected file object ID is required")
        self._policy.authorize(
            envelope, context, signed, operation="investigate", path=path
        )
        reserved = self._checkpoints.reserve(envelope, path, expected_oid)
        try:
            file = self._file(envelope, path, expected_oid)
            content = self._repository.read_blob(file.oid, max_bytes=512 * 1024)
            if content is None:
                raise ExecutionDenied("The file is outside the bounded text adapter")
            self._policy.authorize(
                envelope, context, signed, operation="investigate", path=path
            )
        except Exception:
            self._checkpoints.finish(envelope, reserved, success=False)
            raise
        self._checkpoints.finish(envelope, reserved, success=True)
        return ReadEvidence(envelope.workspace.commit, file.path, file.oid, content)

    def resume(
        self, envelope: ExecutionEnvelope, context: ContextPackage, signed: SignedGrant
    ) -> None:
        checkpoint = self._checkpoints.load(envelope)
        if checkpoint.path is None or checkpoint.oid is None:
            raise ExecutionDenied(
                "Checkpoint has no exact file observation to revalidate"
            )
        self._policy.authorize(
            envelope, context, signed, operation="investigate", path=checkpoint.path
        )
        self._file(envelope, checkpoint.path, checkpoint.oid)
        self._checkpoints.resume(envelope, checkpoint)
