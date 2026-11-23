"""Reviewable changes prepared without writes to the shared checkout."""

from dataclasses import dataclass
from difflib import unified_diff
from hashlib import sha256
from typing import TYPE_CHECKING

from engine.execution.authority import ExecutionDenied

if TYPE_CHECKING:
    from engine.context.package import ContextPackage
    from engine.execution.authority import SignedGrant
    from engine.execution.envelope import ExecutionEnvelope, ExecutionPolicy
    from engine.git.repository import GitRepository


_MAX_EDIT_BYTES = 512 * 1024
_MAX_DIFF_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class TextReplacement:
    path: str
    expected_oid: str
    content: str


@dataclass(frozen=True)
class ChangeReview:
    commit: str
    replacements: tuple[TextReplacement, ...]
    diff: str
    digest: str


def prepare_changes(
    repository: "GitRepository",
    policy: "ExecutionPolicy",
    envelope: "ExecutionEnvelope",
    context: "ContextPackage",
    signed: "SignedGrant",
    replacements: tuple[TextReplacement, ...],
) -> ChangeReview:
    """Check exact committed file versions and produce a review-only diff."""
    if type(replacements) is not tuple or not replacements:
        raise ExecutionDenied("At least one immutable text replacement is required")
    paths = {item.path for item in replacements}
    if len(paths) != len(replacements):
        raise ExecutionDenied("Duplicate replacement path")
    if (
        sum(len(item.content.encode("utf-8")) for item in replacements)
        > _MAX_EDIT_BYTES
    ):
        raise ExecutionDenied("The replacement data exceeds the edit limit")

    commit = envelope.workspace.commit
    differences = []
    for item in sorted(replacements, key=lambda change: change.path):
        if (
            any(char in item.path for char in ("\x00", "\n", "\r", "\t"))
            or "\x00" in item.content
        ):
            raise ExecutionDenied(
                "The text adapter requires printable path boundaries and text content"
            )
        policy.authorize_isolated(
            envelope, context, signed, operation="implement", path=item.path
        )
        files = repository.committed_files(commit, item.path)
        if not any(
            file.path == item.path and file.oid == item.expected_oid for file in files
        ):
            raise ExecutionDenied("The expected committed file version does not match")
        current = repository.read_blob(item.expected_oid, max_bytes=_MAX_EDIT_BYTES)
        if current is None:
            raise ExecutionDenied(
                "The existing file is outside the bounded text adapter"
            )
        differences.extend(
            unified_diff(
                current.splitlines(keepends=True),
                item.content.splitlines(keepends=True),
                fromfile=f"a/{item.path}",
                tofile=f"b/{item.path}",
            )
        )

    diff = "".join(
        line if line.endswith("\n") else f"{line}\n\\ No newline at end of file\n"
        for line in differences
    )
    if not diff or len(diff.encode("utf-8")) > _MAX_DIFF_BYTES:
        raise ExecutionDenied("The review diff is empty or exceeds its byte limit")
    for item in replacements:
        policy.authorize_isolated(
            envelope, context, signed, operation="implement", path=item.path
        )
    return ChangeReview(
        commit, replacements, diff, sha256(diff.encode("utf-8")).hexdigest()
    )
