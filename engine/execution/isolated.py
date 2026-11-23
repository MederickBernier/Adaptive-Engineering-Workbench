"""Run a host-allowlisted check in an ephemeral, unmounted Linux container."""

import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from time import monotonic
from typing import TYPE_CHECKING
from uuid import uuid4

from engine.execution.authority import ExecutionDenied
from engine.execution.changes import ChangeReview, TextReplacement, prepare_changes

if TYPE_CHECKING:
    from engine.context.package import ContextPackage
    from engine.execution.authority import SignedGrant
    from engine.execution.checkpoint import CheckpointStore
    from engine.execution.envelope import ExecutionEnvelope, ExecutionPolicy
    from engine.git.repository import GitRepository


_CHECKPOINT_PATH = "@isolated-check"
_MAX_TREE_BYTES = 8 * 1024 * 1024
_MAX_FILES = 256
_PYTHON = "/usr/local/bin/python"
_BOOTSTRAP = """
import json
import os
import sys
from pathlib import Path

payload = json.load(sys.stdin)
root = Path("/checkout")
for name, text in payload["files"].items():
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
os.chdir(root)
argv = payload["argv"]
os.execve(argv[0], argv, {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "HOME": "/tmp",
    "TMPDIR": "/tmp",
    "PYTHONDONTWRITEBYTECODE": "1",
})
"""


@dataclass(frozen=True)
class CheckResult:
    name: str
    exit_code: int
    review: ChangeReview
    evidence_id: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


class DockerSandbox:
    """Host-side runner with one approved local Docker engine and immutable image."""

    def __init__(self, executable: Path, image: str) -> None:
        if not executable.is_absolute() or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", image
        ):
            raise ValueError(
                "Use an absolute Docker executable and a pinned local image ID"
            )
        host = (
            "npipe:////./pipe/dockerDesktopLinuxEngine"
            if os.name == "nt"
            else "unix:///var/run/docker.sock"
        )
        self._command = (str(executable), "--host", host)
        self.image = image

    def run(self, payload: bytes, *, timeout: float) -> int:
        if timeout <= 0:
            raise ExecutionDenied("Execution deadline is exhausted")
        started = monotonic()
        name = f"aew-check-{uuid4().hex}"
        # Both commands target a host-selected local engine. No host directory or socket is mounted.
        inspect = subprocess.run(
            [
                *self._command,
                "image",
                "inspect",
                "--format",
                "{{json .Config.Volumes}}",
                self.image,
            ],
            capture_output=True,
            check=False,
            timeout=min(timeout, 5),
        )
        if inspect.returncode or inspect.stdout.strip() not in (b"null", b"{}"):
            raise ExecutionDenied(
                "Pinned image is unavailable or declares persistent volumes"
            )
        remaining = timeout - (monotonic() - started)
        if remaining <= 0:
            raise ExecutionDenied("Execution deadline is exhausted")
        try:
            result = subprocess.run(
                [
                    *self._command,
                    "run",
                    "--name",
                    name,
                    "--rm",
                    "--interactive",
                    "--pull=never",
                    "--network=none",
                    "--read-only",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges",
                    "--pids-limit=64",
                    "--memory=256m",
                    "--memory-swap=256m",
                    "--cpus=1",
                    "--log-driver=none",
                    "--no-healthcheck",
                    "--user=65534:65534",
                    "--tmpfs=/checkout:rw,noexec,nosuid,nodev,size=16m,mode=1777",
                    "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
                    "--entrypoint",
                    _PYTHON,
                    self.image,
                    "-I",
                    "-c",
                    _BOOTSTRAP,
                ],
                input=payload,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=remaining,
            )
        except subprocess.TimeoutExpired as error:
            cleanup = subprocess.run(
                [*self._command, "rm", "--force", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
            if cleanup.returncode:
                raise ExecutionDenied(
                    "Timed-out container cleanup could not be confirmed"
                ) from error
            raise ExecutionDenied("Isolated check exceeded its deadline") from error
        if result.returncode in (125, 126, 127):
            raise ExecutionDenied("The isolated check could not be started")
        return result.returncode


class IsolatedChecks:
    """Execute only named checks configured by the trusted host and recorded in a Work Unit."""

    def __init__(
        self,
        repository: "GitRepository",
        policy: "ExecutionPolicy",
        checkpoints: "CheckpointStore",
        sandbox: DockerSandbox,
        checks: dict[str, tuple[str, ...]],
    ) -> None:
        if any(
            not argv or not PurePosixPath(argv[0]).is_absolute()
            for argv in checks.values()
        ):
            raise ValueError("Each check needs an absolute container executable")
        self._repository = repository
        self._policy = policy
        self._checkpoints = checkpoints
        self._sandbox = sandbox
        self._checks = {name: tuple(argv) for name, argv in checks.items()}

    def _request(
        self,
        envelope: "ExecutionEnvelope",
        context: "ContextPackage",
        signed: "SignedGrant",
        replacements: tuple[TextReplacement, ...],
        name: str,
    ) -> tuple[tuple[str, ...], str]:
        argv = self._checks.get(name)
        if argv is None:
            raise ExecutionDenied("Check is outside the host allowlist")
        if (
            type(replacements) is not tuple
            or not replacements
            or len(replacements) > _MAX_FILES
        ):
            raise ExecutionDenied("A bounded set of immutable replacements is required")
        if (
            sum(len(item.content.encode("utf-8")) for item in replacements)
            > _MAX_TREE_BYTES
        ):
            raise ExecutionDenied(
                "The replacement data exceeds the checkout byte limit"
            )
        for item in replacements:
            recorded = self._policy.authorize_isolated(
                envelope,
                context,
                signed,
                operation="run_tests",
                path=item.path,
            )
            if name not in recorded:
                raise ExecutionDenied(
                    "Check is outside the recorded Work Unit verification"
                )
        marker = sha256(
            json.dumps(
                [
                    [asdict(item) for item in replacements],
                    name,
                    argv,
                    self._sandbox.image,
                ],
                sort_keys=True,
            ).encode()
        ).hexdigest()
        return argv, marker

    def _payload(
        self,
        envelope: "ExecutionEnvelope",
        signed: "SignedGrant",
        review: ChangeReview,
        argv: tuple[str, ...],
    ) -> bytes:
        tree = self._repository.committed_files(review.commit, regular_only=True)
        if len(tree) > _MAX_FILES:
            raise ExecutionDenied("Committed checkout exceeds the file-count limit")
        updates = {item.path: item.content for item in review.replacements}
        files = {}
        remaining = _MAX_TREE_BYTES
        for file in tree:
            if self._policy.path_is_protected(file.path, signed.grant):
                continue
            path = PurePosixPath(file.path)
            if path.is_absolute() or any(
                part in ("", ".", "..", ".git") for part in file.path.split("/")
            ):
                raise ExecutionDenied("Committed checkout contains an unsupported path")
            self._checkpoints.remaining_seconds(envelope)
            text = updates.pop(file.path, None)
            if text is None:
                text = self._repository.read_blob(file.oid, max_bytes=remaining)
            if text is None:
                raise ExecutionDenied(
                    "Committed checkout exceeds the text adapter limits"
                )
            remaining -= len(text.encode("utf-8"))
            if remaining < 0:
                raise ExecutionDenied(
                    "Committed checkout exceeds the checkout byte limit"
                )
            files[file.path] = text
        if (
            len(tree) + len(updates) > _MAX_FILES
            or sum(len(text.encode("utf-8")) for text in updates.values()) > remaining
        ):
            raise ExecutionDenied("New files exceed the disposable checkout limits")
        files.update(updates)
        return json.dumps(
            {"argv": argv, "files": files}, separators=(",", ":")
        ).encode()

    def run(
        self,
        envelope: "ExecutionEnvelope",
        context: "ContextPackage",
        signed: "SignedGrant",
        *,
        replacements: tuple[TextReplacement, ...],
        name: str,
    ) -> CheckResult:
        argv, marker = self._request(envelope, context, signed, replacements, name)
        checkpoint = self._checkpoints.reserve(envelope, _CHECKPOINT_PATH, marker)
        try:
            review = prepare_changes(
                self._repository, self._policy, envelope, context, signed, replacements
            )
            payload = self._payload(envelope, signed, review, argv)
            self._request(envelope, context, signed, replacements, name)
            exit_code = self._sandbox.run(
                payload, timeout=self._checkpoints.remaining_seconds(envelope)
            )
            self._request(envelope, context, signed, replacements, name)
        except Exception:
            self._checkpoints.finish(envelope, checkpoint, success=False)
            raise
        evidence = self._checkpoints.finish(
            envelope,
            checkpoint,
            success=True,
            observed_check=(name, exit_code, review.digest, self._sandbox.image),
        )
        assert evidence is not None
        return CheckResult(name, exit_code, review, evidence.evidence_id)

    def resume(
        self,
        envelope: "ExecutionEnvelope",
        context: "ContextPackage",
        signed: "SignedGrant",
        *,
        replacements: tuple[TextReplacement, ...],
        name: str,
    ) -> None:
        checkpoint = self._checkpoints.load(envelope)
        self._checkpoints.remaining_seconds(envelope)
        _, marker = self._request(envelope, context, signed, replacements, name)
        if checkpoint.path != _CHECKPOINT_PATH or checkpoint.oid != marker:
            raise ExecutionDenied(
                "Pending check or reviewed edits do not match the checkpoint"
            )
        prepare_changes(
            self._repository, self._policy, envelope, context, signed, replacements
        )
        self._checkpoints.resume(envelope, checkpoint)
